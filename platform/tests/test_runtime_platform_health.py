"""EPIC-007 (T7) — Runtime platform health tests."""

from __future__ import annotations

import dataclasses
from platform.runtime_platform.core import RuntimeKernel
from platform.runtime_platform.errors import RuntimePlatformError
from platform.runtime_platform.health import HEALTHY, UNHEALTHY, RuntimePlatformHealth
from platform.tests.runtime_platform_helpers import request

import pytest


def test_probe_healthy_on_fresh_kernel():
    report = RuntimePlatformHealth(RuntimeKernel()).probe()
    assert report.status == HEALTHY
    assert report.healthy
    assert all(check.ok for check in report.checks)
    assert len(report.checks) == 3
    assert report.to_dict()["status"] == HEALTHY


def test_probe_unhealthy_on_tampered_registry():
    kernel = RuntimeKernel()
    kernel.submit(request("a"))
    kernel.submit(request("b"))
    reg = kernel.registry
    reg._entries[0] = dataclasses.replace(reg._entries[0], record_sha256="deadbeef")
    report = RuntimePlatformHealth(kernel).probe()
    assert report.status == UNHEALTHY
    assert not report.healthy
    names = {c.name: c.status for c in report.checks}
    assert names["execution-registry-intact"] == UNHEALTHY


def test_check_result_ok_and_dict():
    report = RuntimePlatformHealth(RuntimeKernel()).probe()
    check = report.checks[0]
    assert check.ok
    assert set(check.to_dict()) == {"name", "status", "detail"}


def test_health_rejects_bad_kernel():
    with pytest.raises(RuntimePlatformError):
        RuntimePlatformHealth("bad")  # type: ignore[arg-type]
