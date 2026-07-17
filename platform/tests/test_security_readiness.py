"""EC2-CAP-SEC-001 / SEC-CLASS — readiness validation tests.

Asserts the readiness conditions the determination requires: reuse of certified
components (no duplication), determinism (reproducible evidence with no wall-clock),
and phase discipline (only SEC-CLASS is present — no SEC-INTEL / SEC-REG / SEC-OBS /
SEC-CERT / SEC-ZONE artifacts).
"""

from __future__ import annotations

from pathlib import Path
from platform.security.contracts import ClassificationKind, SubjectLayer
from platform.security.service import build_security_classification_service

_SECURITY_PKG = Path(__file__).resolve().parents[1] / "security"


def test_reuses_certified_foundation_hashing():
    # SEC-CLASS reuses the foundation content hash — it defines no new hashing.
    from platform.security import classification as classification_module

    assert classification_module.content_hash.__module__ == "platform.foundation.contracts"


def test_reuses_certified_identity_seam():
    # SEC-CLASS references the certified L7 AuthorizationService — it defines no authz.
    from platform.security import service as service_module

    assert service_module.AuthorizationService.__module__ == "platform.identity.service"


def test_reuses_certified_capability_group_vocabulary():
    from platform.security import contracts as contracts_module

    assert contracts_module.CapabilityGroup.__module__ == "platform.identity.contracts"


def test_no_new_authorization_logic_is_introduced():
    service = build_security_classification_service()
    assert not hasattr(service, "authorize")
    assert not hasattr(service, "authorize_principal")


def test_evidence_is_deterministic_across_identical_runs():
    def build_fingerprint() -> str:
        service = build_security_classification_service()
        service.classify(
            ClassificationKind.CONFIDENTIALITY,
            SubjectLayer.DATA,
            "UCOS-DATA-000001",
            "restricted",
        )
        service.classify(
            ClassificationKind.INTEGRITY, SubjectLayer.SERVICE, "UCOS-SVC-000001", "signed"
        )
        return service.report().fingerprint()

    assert build_fingerprint() == build_fingerprint()


def test_only_sec_class_modules_are_present():
    # Phase discipline: no future sub-capability modules exist in the package.
    forbidden = {
        "intelligence.py",
        "registries.py",
        "observability.py",
        "zones.py",
        "certification.py",
    }
    present = {p.name for p in _SECURITY_PKG.glob("*.py")}
    assert not (forbidden & present), f"future-phase modules present: {forbidden & present}"


def test_expected_sec_class_modules_are_present():
    expected = {
        "__init__.py",
        "errors.py",
        "contracts.py",
        "classification.py",
        "service.py",
        "bootstrap.py",
    }
    present = {p.name for p in _SECURITY_PKG.glob("*.py")}
    assert expected.issubset(present)


def test_no_secret_material_module_is_introduced():
    # SEC-04: SEC-CLASS ships no secret/credential/key module.
    forbidden = {"secrets.py", "keys.py", "credentials.py", "crypto.py"}
    present = {p.name for p in _SECURITY_PKG.glob("*.py")}
    assert not (forbidden & present)
