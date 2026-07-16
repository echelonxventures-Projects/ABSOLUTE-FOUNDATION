"""Shared pytest fixtures for the EC-1 engine test suite.

Provides small, self-contained registry substrates written to ``tmp_path`` so the
Registry Adapter (EPIC-002) can be exercised without touching the read-only
certified corpus (DP-03). A separate fixture points at the real ``00-BOOK/DATA``
for read-only integration checks (present only when the corpus is available).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.registry.source import (
    ARTIFACTS_FILE,
    RELATIONSHIPS_FILE,
    VOLUMES_FILE,
    RegistrySource,
    default_data_dir,
)

_TRACE_EMPTY = {
    "requirement": [],
    "architecture": [],
    "design": [],
    "implementation": [],
    "source_code": [],
    "unit_test": [],
    "integration_test": [],
    "functional_test": [],
    "security_test": [],
    "certification": [],
    "deployment": [],
    "production": [],
    "operations": [],
}


def _artifact(uid, **overrides):
    base = {
        "universal_id": uid,
        "native_id": None,
        "name": f"Artifact {uid}",
        "description": "",
        "category": "REG",
        "volume": "VOL-000",
        "page_start": 1,
        "page_end": 1,
        "status": "ACTIVE",
        "version": "1.0.0",
        "parent": None,
        "dependencies": [],
        "program": "UKB",
        "owner": "UCOS-PROGRAM-CUSTODIAN",
        "tags": ["UKB", "REG"],
        "path": f"00-BOOK/{uid}.md",
        "return_link": "00-BOOK/UCOS-BOOK-000000-UNIVERSAL-MASTER-KNOWLEDGE-BOOK.md",
        "content_hash": None,
        "traceability": dict(_TRACE_EMPTY),
    }
    base.update(overrides)
    return base


def _edge(edge_id, src, dst, edge_type, inverse_of=None, note="structural:chain"):
    return {
        "edge_id": edge_id,
        "from": src,
        "to": dst,
        "type": edge_type,
        "inverse_of": inverse_of,
        "note": note,
    }


def _volume(vid, serial, name, category, artifact_count, page_start=1, page_end=10):
    return {
        "volume_id": vid,
        "serial": serial,
        "name": name,
        "description": f"Volume {name}.",
        "category": category,
        "status": "ACTIVE",
        "artifact_count": artifact_count,
        "page_range_start": page_start,
        "page_range_end": page_end,
        "index_path": f"00-BOOK/REGISTRIES/VOLUME-REGISTRY.md#{vid.lower()}",
    }


@pytest.fixture
def sample_artifacts():
    """A small, internally-consistent set of artifact records."""
    return [
        _artifact("UCOS-BOOK-000000", name="Root Book", category="BOOK", volume="VOL-000"),
        _artifact(
            "UCOS-REG-000001",
            native_id="REG-001",
            name="Alpha",
            category="REG",
            volume="VOL-000",
            parent="UCOS-BOOK-000000",
            program="UKB",
            status="ACTIVE",
        ),
        _artifact(
            "UCOS-ENG-000001",
            native_id="ENG-001",
            name="Beta",
            category="ENG",
            volume="VOL-003",
            parent="UCOS-BOOK-000000",
            program="ENG",
            status="FROZEN",
            dependencies=["UCOS-REG-000001"],
        ),
    ]


@pytest.fixture
def sample_relationships():
    """Edges over the sample artifacts (Parent/Child + Depends-On)."""
    return [
        _edge("UEDGE-000000001", "UCOS-REG-000001", "UCOS-BOOK-000000", "Parent"),
        _edge("UEDGE-000000002", "UCOS-BOOK-000000", "UCOS-REG-000001", "Child"),
        _edge("UEDGE-000000003", "UCOS-ENG-000001", "UCOS-REG-000001", "Depends-On"),
        _edge("UEDGE-000000004", "UCOS-ENG-000001", "UCOS-BOOK-000000", "Parent"),
    ]


@pytest.fixture
def sample_volumes():
    """Volumes matching the sample artifact placement counts."""
    return [
        _volume("VOL-000", 0, "MASTER INDEX", "IDX", artifact_count=2),
        _volume("VOL-003", 3, "ARCHITECTURE", "ARCH", artifact_count=1),
    ]


@pytest.fixture
def data_dir(tmp_path, sample_artifacts, sample_relationships, sample_volumes) -> Path:
    """Write a complete sample substrate to a temp dir and return its path."""
    (tmp_path / ARTIFACTS_FILE).write_text(
        json.dumps(
            {"generated_at": "2026-07-16T00:00:00+00:00", "count": len(sample_artifacts),
             "artifacts": sample_artifacts}
        ),
        encoding="utf-8",
    )
    (tmp_path / RELATIONSHIPS_FILE).write_text(
        json.dumps({"count": len(sample_relationships), "relationships": sample_relationships}),
        encoding="utf-8",
    )
    (tmp_path / VOLUMES_FILE).write_text(
        json.dumps({"count": len(sample_volumes), "volumes": sample_volumes}),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def source(data_dir) -> RegistrySource:
    """A RegistrySource over the sample substrate."""
    return RegistrySource(data_dir)


@pytest.fixture
def real_data_dir() -> Path:
    """The real, read-only 00-BOOK/DATA directory (skips if unavailable)."""
    path = default_data_dir()
    if not path.is_dir():
        pytest.skip("00-BOOK/DATA registry substrate not present")
    return path



# --------------------------------------------------------------------------- #
# EPIC-003 (Compiler Core) fixtures — a certified provenance substrate plus    #
# ready-made BP-DATA blueprint documents. Everything lives under tmp_path so    #
# the compiler never touches the read-only corpus (DP-03).                      #
# --------------------------------------------------------------------------- #

from engine.registry.adapter import RegistryAdapter  # noqa: E402

# The six provenance-chain sources a BP-DATA blueprint references (IMP-007 §1).
# These mirror the real, certified 00-BOOK data-family artifacts.
_PROVENANCE_SOURCES = {
    "canonical_source": "UCOS-DAT-000007",
    "reference_architecture": "UCOS-REF-000003",
    "runtime_catalog": "UCOS-CAT-000003",
    "architecture_constitution": "UCOS-DAT-000002",
    "ontology_root": "UCOS-DAT-000004",
    "generation_framework": "UCOS-GEN-000003",
}


@pytest.fixture
def compiler_artifacts():
    """Registered, certified (ACTIVE) provenance sources for BP-DATA compilation.

    Includes one deliberately non-certified artifact (``UCOS-DAT-000099`` in
    IN_PROGRESS) so tests can exercise the 'reject uncertified source' path.
    """
    records = [_artifact("UCOS-BOOK-000000", name="Root Book", category="BOOK", volume="VOL-000")]
    for uid in _PROVENANCE_SOURCES.values():
        records.append(
            _artifact(
                uid,
                name=f"Certified source {uid}",
                category=uid.split("-")[1],
                volume="VOL-006",
                parent="UCOS-BOOK-000000",
                status="ACTIVE",
            )
        )
    records.append(
        _artifact(
            "UCOS-DAT-000099",
            name="Uncertified data source",
            category="DAT",
            volume="VOL-006",
            parent="UCOS-BOOK-000000",
            status="IN_PROGRESS",
        )
    )
    return records


@pytest.fixture
def compiler_data_dir(tmp_path, compiler_artifacts):
    """A registry substrate (artifacts only) sufficient for the compiler."""
    (tmp_path / ARTIFACTS_FILE).write_text(
        json.dumps({"count": len(compiler_artifacts), "artifacts": compiler_artifacts}),
        encoding="utf-8",
    )
    (tmp_path / RELATIONSHIPS_FILE).write_text(
        json.dumps({"count": 0, "relationships": []}), encoding="utf-8"
    )
    (tmp_path / VOLUMES_FILE).write_text(
        json.dumps({"count": 0, "volumes": []}), encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def compiler_registry(compiler_data_dir) -> RegistryAdapter:
    """A Registry Adapter over the certified compiler substrate."""
    return RegistryAdapter.open(compiler_data_dir)


@pytest.fixture
def data_blueprint() -> dict:
    """A valid, certified BP-DATA blueprint document (the BP-DATA success case)."""
    return {
        "ir_version": "1.0.0",
        "blueprint_id": "BP-DATA-0001",
        "family": "BP-DATA",
        "name": "Customer",
        "version": "1.0.0",
        "description": "Customer master-data entity.",
        "certification": {"status": "CERTIFIED", "evidence": "UCOS-DAT-000018"},
        "provenance": dict(_PROVENANCE_SOURCES),
        "dependencies": [],
        "entity": {
            "name": "Customer",
            "table": "customer",
            "attributes": [
                {"name": "id", "data_type": "uuid", "nullable": False, "primary_key": True},
                {
                    "name": "email",
                    "data_type": "string",
                    "nullable": False,
                    "unique": True,
                    "max_length": 320,
                },
                {"name": "created_at", "data_type": "timestamp", "nullable": False},
            ],
            "indexes": [
                {"name": "ix_customer_email", "columns": ["email"], "unique": True}
            ],
            "relationships": [
                {"name": "orders", "target": "BP-DATA-0002", "kind": "one_to_many"}
            ],
        },
    }


@pytest.fixture
def dependency_blueprint() -> dict:
    """A second BP-DATA blueprint that BP-DATA-0001 can depend on."""
    return {
        "ir_version": "1.0.0",
        "blueprint_id": "BP-DATA-0002",
        "family": "BP-DATA",
        "name": "Order",
        "version": "1.0.0",
        "certification": {"status": "CERTIFIED", "evidence": "UCOS-DAT-000018"},
        "provenance": dict(_PROVENANCE_SOURCES),
        "dependencies": [],
        "entity": {
            "name": "Order",
            "table": "order_line",
            "attributes": [
                {"name": "id", "data_type": "uuid", "nullable": False, "primary_key": True},
                {"name": "total", "data_type": "decimal", "nullable": False},
            ],
        },
    }



# --------------------------------------------------------------------------- #
# EPIC-005 (Runtime Assembly) fixtures — a real published compiler package on   #
# disk plus the signer that produced it, so the runtime engine can be exercised #
# end to end against a genuine EPIC-003 artifact (never the certified corpus).  #
# --------------------------------------------------------------------------- #

from engine.compiler.pipeline import CompilerPipeline  # noqa: E402
from engine.compiler.signing import Signer  # noqa: E402

#: A non-secret, fixed runtime-assembly signing key (a test fixture, never a
#: production credential — production keys remain by-reference via env://).
RUNTIME_SIGNING_KEY = b"ec1-runtime-assembly-test-key"


@pytest.fixture
def runtime_signer() -> Signer:
    """The signer that both signs and verifies the published test package."""
    return Signer(key=RUNTIME_SIGNING_KEY)


@pytest.fixture
def published_package(tmp_path, compiler_registry, data_blueprint, runtime_signer):
    """Compile BP-DATA-0001 through the real pipeline and publish it to disk.

    Returns the :class:`PublishedArtifact` (its ``output_dir`` holds
    ``manifest.json``, ``sbom.json``, ``signature.json``, ``artifact-record.json``
    and ``artifacts/**``) — a genuine EPIC-003 published compiler package.
    """
    output_dir = tmp_path / "published"
    pipeline = CompilerPipeline(compiler_registry, signer=runtime_signer, output_dir=output_dir)
    result = pipeline.compile_one(data_blueprint)
    assert result.success and result.published is not None
    return result.published


@pytest.fixture
def dependency_published_package(
    tmp_path, compiler_registry, dependency_blueprint, runtime_signer
):
    """A second published package (BP-DATA-0002) usable as a dependency closure member."""
    output_dir = tmp_path / "published-dep"
    pipeline = CompilerPipeline(compiler_registry, signer=runtime_signer, output_dir=output_dir)
    result = pipeline.compile_one(dependency_blueprint)
    assert result.success and result.published is not None
    return result.published
