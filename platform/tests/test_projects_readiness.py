"""EC2-EPIC-005 — project readiness validation tests.

Asserts the readiness conditions the determination requires: reuse of the certified
Foundation / Identity / Observability / Workspace components (no duplication), no new
authorization logic, determinism (reproducible evidence with no wall-clock), the full
13-module package topology, and the absence of any secret-material module.
"""

from __future__ import annotations

from pathlib import Path
from platform.foundation.bootstrap import bootstrap_platform
from platform.foundation.identity import Principal, Role
from platform.identity.service import bootstrap_identity, build_authorization_service
from platform.projects.bootstrap import bootstrap_projects
from platform.projects.contracts import AssociationKind, ProjectStatus
from platform.workspace.registration import WorkspaceRegistry

_PROJECTS_PKG = Path(__file__).resolve().parents[1] / "projects"


def test_reuses_certified_foundation_hashing():
    from platform.projects import contracts as contracts_module

    assert contracts_module.content_hash.__module__ == "platform.foundation.contracts"


def test_reuses_certified_identity_seam():
    from platform.projects import service as service_module

    assert service_module.AuthorizationService.__module__ == "platform.identity.service"


def test_reuses_certified_observability_health_model():
    from platform.projects import health as health_module

    assert health_module.HealthStatus.__module__ == "platform.observability.contracts"
    assert health_module.HealthCheck.__module__ == "platform.observability.health"


def test_reuses_certified_workspace_isolation_rule():
    # No second isolation rule — the certified workspace tenants_isolated is reused.
    from platform.projects import search as search_module
    from platform.projects import service as service_module

    assert search_module.tenants_isolated.__module__ == "platform.workspace.isolation"
    assert service_module.tenants_isolated.__module__ == "platform.workspace.isolation"


def test_reuses_certified_workspace_registry_for_parent_binding():
    from platform.projects import service as service_module

    assert service_module.WorkspaceRegistry.__module__ == "platform.workspace.registration"


def test_no_new_authorization_logic_is_introduced():
    auth = build_authorization_service()
    service = bootstrap_projects  # symbol exists
    assert callable(service)
    from platform.projects.service import build_project_service

    svc = build_project_service(authorization=auth, workspaces=WorkspaceRegistry())
    assert not hasattr(svc, "authorize")
    assert not hasattr(svc, "authorize_principal")


def test_all_thirteen_modules_are_present():
    expected = {
        "__init__.py",
        "errors.py",
        "metadata.py",
        "contracts.py",
        "lifecycle.py",
        "registry.py",
        "associations.py",
        "status.py",
        "context.py",
        "search.py",
        "health.py",
        "service.py",
        "bootstrap.py",
    }
    present = {p.name for p in _PROJECTS_PKG.glob("*.py")}
    assert expected.issubset(present)


def test_no_secret_material_module_is_introduced():
    forbidden = {"secrets.py", "keys.py", "credentials.py", "crypto.py"}
    present = {p.name for p in _PROJECTS_PKG.glob("*.py")}
    assert not (forbidden & present)


def test_evidence_is_deterministic_across_identical_runs():
    def build_fingerprint() -> str:
        context = bootstrap_platform()
        auth = bootstrap_identity(context)
        service = bootstrap_projects(context, authorization=auth)
        admin = Principal.create("admin@x", [Role.PLATFORM_ADMINISTRATOR])
        session = auth.establish_session(admin, issued_at=0, ttl=1000)
        ws = service.workspaces.create("team", "Team", admin.subject)
        project = service.create_project(
            session.session_id, "alpha", "Alpha", ws.workspace_id, now=1
        )
        service.add_association(
            session.session_id, project.project_id, AssociationKind.BLUEPRINT, "BP-1", now=2
        )
        service.transition(session.session_id, project.project_id, ProjectStatus.COMPLETED, now=3)
        return service.evidence().fingerprint()

    assert build_fingerprint() == build_fingerprint()
