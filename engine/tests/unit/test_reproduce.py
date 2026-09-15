"""TASK-000032/000034 — Reproducibility harness tests.

Verifies blueprint resolution, the byte-level comparison engine, diff-report
generation, successful double builds, and deliberate divergence detection — all
over the temp compiler substrate so the corpus is never touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.determinism.errors import (
    BlueprintResolutionError,
    NonDeterministicOutputError,
    ReproducibilityError,
)
from engine.determinism.reproduce import (
    DEFAULT_BLUEPRINTS_DIR,
    DirectoryBlueprintProvider,
    ReproducibilityResult,
    compare_builds,
    double_build,
)

# -- blueprint provider -------------------------------------------------------


def test_default_provider_resolves_shipped_bp_data_0001():
    provider = DirectoryBlueprintProvider()
    doc = provider.get("BP-DATA-0001")
    assert doc["blueprint_id"] == "BP-DATA-0001"
    assert doc["certification"]["status"] == "CERTIFIED"
    assert provider.directory == DEFAULT_BLUEPRINTS_DIR


def test_provider_rejects_invalid_id():
    with pytest.raises(BlueprintResolutionError):
        DirectoryBlueprintProvider().get("../etc/passwd")


def test_provider_missing_blueprint(tmp_path):
    with pytest.raises(BlueprintResolutionError):
        DirectoryBlueprintProvider(tmp_path).get("BP-DATA-9999")


# -- comparison engine --------------------------------------------------------


def _plant(base: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return base


def test_compare_builds_identical(tmp_path):
    files = {
        "artifacts/schema/customer.sql": "CREATE TABLE customer();\n",
        "manifest.json": "{}\n",
        "sbom.json": "{}\n",
        "signature.json": "{}\n",
        "artifact-record.json": "{}\n",
    }
    a = _plant(tmp_path / "a", files)
    b = _plant(tmp_path / "b", files)
    diffs, categories = compare_builds(a, b)
    assert all(d.is_identical for d in diffs)
    assert all(categories.values())


def test_compare_builds_detects_content_divergence(tmp_path):
    base = {
        "artifacts/schema/customer.sql": "A\n",
        "manifest.json": "{}\n",
        "sbom.json": "{}\n",
        "signature.json": "{}\n",
        "artifact-record.json": "{}\n",
    }
    a = _plant(tmp_path / "a", base)
    b = _plant(tmp_path / "b", {**base, "artifacts/schema/customer.sql": "B\n"})
    diffs, categories = compare_builds(a, b)
    assert categories["generated_source"] is False
    assert categories["manifests"] is True
    differing = [d for d in diffs if d.status == "differs"]
    assert differing[0].path == "artifacts/schema/customer.sql"


def test_compare_builds_detects_missing_file(tmp_path):
    a = _plant(tmp_path / "a", {"manifest.json": "{}\n", "sbom.json": "{}\n"})
    b = _plant(tmp_path / "b", {"manifest.json": "{}\n", "signature.json": "{}\n"})
    diffs, categories = compare_builds(a, b)
    statuses = {d.path: d.status for d in diffs}
    assert statuses["sbom.json"] == "only_in_a"
    assert statuses["signature.json"] == "only_in_b"
    assert categories["sbom"] is False
    assert categories["signatures"] is False
    # categories with no files present are not asserted identical
    assert categories["publication_payloads"] is False


# -- successful double build --------------------------------------------------


def test_double_build_is_byte_identical(compiler_registry):
    result = double_build("BP-DATA-0001", registry=compiler_registry)
    assert isinstance(result, ReproducibilityResult)
    assert result.byte_identical is True
    assert result.artifact_id_a == result.artifact_id_b
    assert result.divergences == ()
    assert all(result.category_identical.values())
    assert len(result.diffs) == 7  # 3 artifacts + manifest + sbom + signature + record


def test_double_build_report_dict_shape(compiler_registry):
    result = double_build("BP-DATA-0001", registry=compiler_registry)
    report = result.to_report_dict()
    assert report["reproducibility_report"] is True
    assert report["byte_identical"] is True
    assert report["artifact_id_match"] is True
    assert set(report["categories"]) == {
        "generated_source",
        "manifests",
        "sbom",
        "signatures",
        "publication_payloads",
    }
    assert report["divergence_count"] == 0


def test_double_build_writes_report(compiler_registry, tmp_path):
    result = double_build("BP-DATA-0001", registry=compiler_registry)
    path = result.write_report(tmp_path / "reproducibility_report.json")
    assert path.is_file()
    on_disk = json.loads(path.read_text())
    assert on_disk["blueprint_id"] == "BP-DATA-0001"


def test_double_build_accepts_explicit_signing_key(compiler_registry):
    result = double_build("BP-DATA-0001", registry=compiler_registry, signing_key=b"custom-key")
    assert result.byte_identical


def test_double_build_accepts_key_ref(compiler_registry, monkeypatch):
    monkeypatch.setenv("UCOS_DET_KEY", "ref-key")
    result = double_build("BP-DATA-0001", registry=compiler_registry, key_ref="env://UCOS_DET_KEY")
    assert result.byte_identical


def test_double_build_failed_build_raises(compiler_registry, tmp_path):
    # An uncertified blueprint cannot be compiled → reproducibility build fails.
    doc = json.loads((DEFAULT_BLUEPRINTS_DIR / "BP-DATA-0001.json").read_text())
    doc["certification"] = {"status": "UNCERTIFIED", "evidence": ""}
    (tmp_path / "BP-DATA-0002.json").write_text(
        json.dumps({**doc, "blueprint_id": "BP-DATA-0002"}), encoding="utf-8"
    )
    provider = DirectoryBlueprintProvider(tmp_path)
    with pytest.raises(ReproducibilityError) as exc:
        double_build("BP-DATA-0002", registry=compiler_registry, provider=provider)
    assert "gap" in exc.value.context


# -- deliberate divergence detection ------------------------------------------


def test_double_build_detects_injected_divergence(compiler_registry, monkeypatch):
    import engine.determinism.reproduce as reproduce

    real = reproduce._execute_build
    state = {"n": 0}

    def _diverging(**kwargs):
        base = real(**kwargs)
        state["n"] += 1
        if state["n"] == 2:  # mutate the second (B) build to force divergence
            (base / "artifacts" / "schema" / "customer.sql").write_text(
                "-- tampered\n", encoding="utf-8"
            )
        return base

    monkeypatch.setattr(reproduce, "_execute_build", _diverging)
    result = double_build("BP-DATA-0001", registry=compiler_registry)
    assert result.byte_identical is False
    assert result.category_identical["generated_source"] is False
    assert len(result.divergences) >= 1


def test_double_build_strict_raises_on_divergence(compiler_registry, monkeypatch):
    import engine.determinism.reproduce as reproduce

    real = reproduce._execute_build
    state = {"n": 0}

    def _diverging(**kwargs):
        base = real(**kwargs)
        state["n"] += 1
        if state["n"] == 2:
            (base / "manifest.json").write_text("{tampered}\n", encoding="utf-8")
        return base

    monkeypatch.setattr(reproduce, "_execute_build", _diverging)
    with pytest.raises(NonDeterministicOutputError) as exc:
        double_build("BP-DATA-0001", registry=compiler_registry, strict=True)
    assert exc.value.code == "DET-DIVERGENCE-001"
