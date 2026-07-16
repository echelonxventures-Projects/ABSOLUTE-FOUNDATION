"""TASK-000041 — Generation Orchestrator (EPIC-006).

The single execution path of the Factory Layer. For each request it:

    1. **resolves the blueprint** document through an injected
       :class:`~engine.determinism.reproduce.BlueprintProvider` (no direct
       filesystem scanning by the orchestrator);
    2. **resolves the classification** from registry metadata — the registered
       :class:`~engine.registry.models.Artifact` when the blueprint is registered,
       otherwise the blueprint document's declared metadata;
    3. **resolves the factory** via the :class:`~engine.factory.registry.FactoryRegistry`;
    4. **executes the compiler pipeline** (EPIC-003) through the RegistryAdapter,
       which enforces certification and family support;
    5. **executes the runtime pipeline** (EPIC-005) — assembly + deployment +
       rollback — on the published artifact;
    6. **produces a** :class:`~engine.factory.contracts.FactoryResult` with a
       deterministic Generation Evidence Record.

It bypasses nothing: registry access is via the RegistryAdapter, certification and
family gates are the compiler's own, disclosure is the runtime's own, and no
artifacts are invented — a class the compiler defers yields a faithful **gap**
result carrying the compiler's Gap Report (TP-01). Every factory reuses this exact
`execute` path, so there is no duplicated pipeline logic and no special-case route.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from engine.compiler.pipeline import CompilationResult, CompilerPipeline
from engine.compiler.signing import Signer
from engine.determinism.reproduce import BlueprintProvider, DirectoryBlueprintProvider
from engine.factory.classifier import BlueprintClassification, resolve_blueprint_class
from engine.factory.contracts import (
    FactoryRequest,
    FactoryResult,
    GenerationStatus,
)
from engine.factory.errors import BlueprintResolutionError
from engine.factory.evidence import build_generation_evidence
from engine.factory.factories.base import ExecutionContext
from engine.factory.registry import FactoryRegistry
from engine.foundation.obs.logging import get_logger
from engine.foundation.obs.telemetry import trace
from engine.registry.adapter import RegistryAdapter
from engine.runtime import assemble, descriptor, disclosure_present, rollback

_logger = get_logger("factory.orchestrator")


class GenerationOrchestrator:
    """Drives classification → factory → compiler → runtime for one blueprint."""

    __slots__ = ("_registry", "_factories", "_provider", "_signer", "_output_dir")

    def __init__(
        self,
        *,
        registry: RegistryAdapter,
        factories: FactoryRegistry,
        signer: Signer,
        output_dir: str | Path,
        provider: BlueprintProvider | None = None,
    ) -> None:
        self._registry = registry
        self._factories = factories
        self._signer = signer
        self._output_dir = Path(output_dir)
        self._provider = provider if provider is not None else DirectoryBlueprintProvider()

    @property
    def factories(self) -> FactoryRegistry:
        return self._factories

    # -- public API ------------------------------------------------------------

    def generate(self, request: FactoryRequest) -> FactoryResult:
        """Generate a single blueprint through the uniform factory path."""
        with trace("factory.generate", blueprint=request.blueprint_id):
            document = self._resolve_blueprint(request.blueprint_id)
            classification = self._classify(request.blueprint_id, document)
            factory = self._factories.resolve_factory(classification)
            context = ExecutionContext(
                request=request,
                document=document,
                classification=classification,
                descriptor=factory.descriptor,
            )
            # Every factory reuses this exact execution path (delegates to execute).
            result = factory.generate(context, self)
        _logger.info(
            "factory.generated",
            blueprint=request.blueprint_id,
            blueprint_class=classification.value,
            factory=factory.descriptor.name,
            status=result.status.value,
        )
        return result

    # -- FactoryExecution (shared execution path) ------------------------------

    def execute(self, context: ExecutionContext) -> FactoryResult:
        """The one and only compile + assemble path (reused by every factory)."""
        document = context.document
        version = str(document.get("version", ""))

        compilation = self._compile(document)
        if not compilation.success or compilation.published is None:
            return self._gap_result(context, version, compilation)
        return self._generated_result(context, version, compilation)

    # -- stages ----------------------------------------------------------------

    def _resolve_blueprint(self, blueprint_id: str) -> Mapping[str, Any]:
        try:
            return self._provider.get(blueprint_id)
        except Exception as exc:  # provider-specific resolution failure  # noqa: BLE001
            raise BlueprintResolutionError(
                "could not resolve blueprint input document",
                blueprint_id=blueprint_id,
                detail=str(exc),
            ) from exc

    def _classify(
        self, blueprint_id: str, document: Mapping[str, Any]
    ) -> BlueprintClassification:
        """Classify from the registered artifact metadata if present, else the doc."""
        artifact = self._registry.artifacts.find(blueprint_id)
        if artifact is not None:
            return resolve_blueprint_class(artifact)
        return resolve_blueprint_class(document)

    def _compile(self, document: Mapping[str, Any]) -> CompilationResult:
        pipeline = CompilerPipeline(
            self._registry, signer=self._signer, output_dir=self._output_dir
        )
        return pipeline.compile_one(document)

    def _generated_result(
        self,
        context: ExecutionContext,
        version: str,
        compilation: CompilationResult,
    ) -> FactoryResult:
        published = compilation.published
        assert published is not None  # guaranteed by caller  # noqa: S101
        env = context.request.environment
        unit = assemble(published, verify_with=self._signer, environment=env)
        # Exercise the full runtime pipeline (deployment + rollback are reversible).
        descriptor(unit, environment=env)
        rollback(unit)

        closure = tuple(unit.closure_records())
        evidence = build_generation_evidence(
            blueprint_id=context.request.blueprint_id,
            blueprint_version=version,
            classification=context.classification,
            compiler_artifact={
                "artifact_id": published.artifact_id,
                "package_sha256": unit.package_sha256,
            },
            runtime_artifact={
                "runtime_id": unit.runtime_id,
                "image_reference": unit.image_reference,
            },
            dependency_closure=closure,
            disclosure=unit.disclosure,
        )
        return FactoryResult(
            blueprint_id=context.request.blueprint_id,
            blueprint_class=context.classification.value,
            factory_name=context.descriptor.name,
            status=GenerationStatus.GENERATED,
            success=True,
            artifact_id=published.artifact_id,
            runtime_id=unit.runtime_id,
            package_sha256=unit.package_sha256,
            image_reference=unit.image_reference,
            dependency_closure=closure,
            disclosure_present=disclosure_present(unit.disclosure),
            evidence=evidence.to_dict(),
        )

    def _gap_result(
        self,
        context: ExecutionContext,
        version: str,
        compilation: CompilationResult,
    ) -> FactoryResult:
        """A faithful gap outcome — no artifacts invented (TP-01)."""
        gap = (
            compilation.gap_report.to_dict()
            if compilation.gap_report is not None
            else {"message": "compilation produced no artifact"}
        )
        evidence = build_generation_evidence(
            blueprint_id=context.request.blueprint_id,
            blueprint_version=version,
            classification=context.classification,
            compiler_artifact=None,
            runtime_artifact=None,
            dependency_closure=(),
            disclosure=None,
            gap=gap,
        )
        return FactoryResult(
            blueprint_id=context.request.blueprint_id,
            blueprint_class=context.classification.value,
            factory_name=context.descriptor.name,
            status=GenerationStatus.GAP,
            success=False,
            dependency_closure=(),
            disclosure_present=False,
            evidence=evidence.to_dict(),
            gap=gap,
        )


__all__ = ["GenerationOrchestrator"]
