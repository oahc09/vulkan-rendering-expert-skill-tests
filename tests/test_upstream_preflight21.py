"""Host-only version and prerequisite routing. No runtime pass is produced."""
import json

import pytest

from tools.delivery19 import upstream_preflight
from tools.evidence19 import vvl_host_wait_result


def test_apple_legacy_and_announced_sdk_branches():
    legacy = dict(probe="apple", os="macOS", architecture="x86_64",
                  macos_major=26, driver_id="VK_DRIVER_ID_MOLTENVK",
                  headers_sha256="a"*64, subset_in_headers=True, subset_advertised=True)
    assert upstream_preflight(legacy)["status"] == "LEGACY_PORTABILITY_PROBE"
    assert upstream_preflight(legacy | {"subset_in_headers": False}) == {
        "status": "REQUIRES_REVIEWED_LEGACY_BUILD", "execution": "NOT_RUN",
    }

    candidate = legacy | {"driver_id": "VK_DRIVER_ID_MESA_KOSMICKRISP", "subset_advertised": False}
    assert upstream_preflight(candidate)["status"] == "OUT_OF_SCOPE"
    assert upstream_preflight(candidate | {"architecture": "arm64"}) == {
        "status": "KOSMICKRISP_PROBE", "execution": "NOT_RUN",
    }
    assert upstream_preflight(candidate | {"architecture": "arm64", "macos_major": 25})["status"] == "OUT_OF_SCOPE"


def test_cross_queue_vvl_ab_preconditions_are_independent():
    facts = dict(probe="vvl_host_wait", program_sha256="a"*64, driver_sha256="b"*64,
                 old_layer_sha256="c"*64, fixed_layer_sha256="d"*64,
                 fixed_commit_verified=True, timeline_enabled=True, sync_validation_enabled=True,
                 same_family_transfer_queue_count=2)
    assert upstream_preflight(facts) == {"status": "VVL_AB_PROBE", "execution": "NOT_RUN"}
    for update in ({"same_family_transfer_queue_count": 1}, {"timeline_enabled": False},
                   {"sync_validation_enabled": False}, {"fixed_commit_verified": False},
                   {"fixed_layer_sha256": "c"*64}):
        assert upstream_preflight(facts | update)["status"] == "PREREQUISITES_UNMET"
    assert upstream_preflight(facts | {"driver_sha256": None})["status"] == "MISSING_INPUT"


def gtest_record(suite, name, **changes):
    row = dict(name=name, classname=suite, status="RUN", result="COMPLETED")
    row.update(changes)
    return json.dumps({"testsuites": [{"name": suite, "testsuite": [row]}]}).encode()


def test_vvl_replay_reader_retains_skip_and_records_only_the_pinned_result():
    suite = "PositiveSyncValTimelineSemaphore"
    name = "HostWaitPreservesCrossQueueDependency"
    assert vvl_host_wait_result(gtest_record(suite, name, result="SKIPPED"), "positive")["status"] == "NOT_RUN"
    failure = gtest_record(suite, name, failures=[{"failure": "SYNC-HAZARD-WRITE-AFTER-WRITE"}])
    observed = vvl_host_wait_result(failure, "positive")
    assert observed["status"] == "FAIL" and observed["write_hazard_in_failures"]
    assert vvl_host_wait_result(gtest_record(suite, name), "positive")["status"] == "PASS"
    negative = gtest_record("NegativeSyncValTimelineSemaphore", "WaitInitialValueTwoQueues")
    assert vvl_host_wait_result(negative, "negative")["layer_and_device_identity"] == "REQUIRES_SEPARATE_CAPTURE"
    with pytest.raises(ValueError, match="pinned filtered"):
        vvl_host_wait_result(negative, "positive")


def test_mesa_anv_replay_requires_matching_driver_and_image_sequence():
    matching = dict(probe="mesa_anv_clear", mesa_version="26.3.1",
                    driver_id="VK_DRIVER_ID_INTEL_OPEN_SOURCE_MESA", platform="Intel LNL",
                    same_command_buffer=True, same_storage_image=True)
    assert upstream_preflight(matching) == {"status": "ANV_CLEAR_REPLAY_ELIGIBLE", "execution": "NOT_RUN"}
    assert upstream_preflight(matching | {"driver_id": "VK_DRIVER_ID_MESA_LLVMPIPE"})["status"] == "OUT_OF_SCOPE"
    assert upstream_preflight(matching | {"same_storage_image": False})["status"] == "OUT_OF_SCOPE"


def test_quick_boot_replay_requires_exact_guest_and_snapshot():
    matching = dict(probe="emulator_quick_boot", host_os="Windows", emulator_version="37.3.10",
                    guest_api="37.1", quick_boot_snapshot=True)
    assert upstream_preflight(matching) == {"status": "QUICK_BOOT_REPLAY_ELIGIBLE", "execution": "NOT_RUN"}
    assert upstream_preflight(matching | {"guest_api": "37.0"})["status"] == "OUT_OF_SCOPE"
    assert upstream_preflight(matching | {"quick_boot_snapshot": False})["status"] == "OUT_OF_SCOPE"
