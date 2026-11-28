"""VUID-shaped positive and one-factor counterexamples; no Vulkan invocation."""
import copy
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from tools.video_inline_query20 import ENCODE_FEEDBACK, STATUS_ONLY, assess
sys.path.pop(0)

pytestmark = pytest.mark.candidate19


def facts(direction="decode"):
    profile = {
        "codec_operation": f"VK_VIDEO_CODEC_OPERATION_{direction.upper()}_H264_BIT_KHR",
        "chroma_subsampling": 2,
        "luma_bit_depth": 1,
        "chroma_bit_depth": 1,
        "profile_chain": {"h264": {"std_profile_idc": 100}},
    }
    if direction == "decode":
        profile["profile_chain"]["h264"]["picture_layout"] = 0
    return {
        "direction": direction, "extension_supported": True, "extension_enabled": True,
        "feature_supported": True, "feature_enabled": True, "session_inline_flag": True,
        "request_inline": True, "explicit_begin_query": False, "session_profile": profile,
        "pool": {"type": STATUS_ONLY, "size": 8, "profile": copy.deepcopy(profile)},
        "first_query": 7, "query_count": 1, "target_slot_available": False,
        "queue_status_support": True,
    }


@pytest.mark.parametrize("direction,query_type", [
    ("decode", STATUS_ONLY), ("encode", STATUS_ONLY), ("encode", ENCODE_FEEDBACK),
])
def test_legal_typed_selection_is_never_execution(direction, query_type):
    plan = facts(direction)
    pool = plan["pool"]
    pool["type"] = query_type
    pool["profile"] = dict(reversed(list(pool["profile"].items())))
    if query_type == ENCODE_FEEDBACK:
        plan["queue_status_support"] = None  # STATUS-only requirement does not transfer.
    assert assess(**plan) == {
        "status": "INLINE_QUERY_METADATA_ADMISSIBLE", "vuids": [],
        "evidence": "CALLER_DECLARED_OFFLINE_ONLY", "runtime_execution": "NOT_RUN",
    }


@pytest.mark.parametrize("direction,field,clause", [
    ("decode", "count", "pNext-08365"), ("encode", "count", "pNext-08360"),
    ("decode", "available", "pNext-08366"), ("encode", "available", "pNext-08361"),
    ("decode", "type", "queryType-08367"), ("encode", "type", "queryType-08362"),
    ("decode", "profile", "queryPool-08368"), ("encode", "profile", "queryPool-08363"),
    ("decode", "queue", "queryType-08369"), ("encode", "queue", "queryType-08364"),
])
def test_one_factor_counterexample_maps_to_pinned_vuid(direction, field, clause):
    plan = facts(direction)
    if field == "count":
        plan.update(first_query=6, query_count=2)
    elif field == "available":
        plan["target_slot_available"] = True
    elif field == "type":
        plan["pool"]["type"] = ENCODE_FEEDBACK if direction == "decode" else "VK_QUERY_TYPE_OCCLUSION"
    elif field == "profile":
        plan["pool"]["profile"]["profile_chain"]["h264"]["std_profile_idc"] = 77
    elif field == "queue":
        plan["queue_status_support"] = False
    result = assess(**plan)
    assert result["status"] == "INLINE_QUERY_CONTRACT_REJECTED"
    assert result["vuids"] == [f"VUID-vkCmd{direction.title()}VideoKHR-{clause}"]


@pytest.mark.parametrize("first,count,expected", [
    (8, 0, ["VUID-VkVideoInlineQueryInfoKHR-queryPool-08372", "VUID-vkCmdDecodeVideoKHR-pNext-08365"]),
    (8, 1, ["VUID-VkVideoInlineQueryInfoKHR-queryPool-08372", "VUID-VkVideoInlineQueryInfoKHR-queryPool-08373"]),
    (7, 2, ["VUID-VkVideoInlineQueryInfoKHR-queryPool-08373", "VUID-vkCmdDecodeVideoKHR-pNext-08365"]),
])
def test_first_and_span_have_independent_boundaries(first, count, expected):
    plan = facts()
    plan.update(first_query=first, query_count=count)
    assert assess(**plan)["vuids"] == expected


@pytest.mark.parametrize("diff,expected", [
    ({"extension_supported": None}, "EXTENSION_NOT_QUERIED"),
    ({"extension_supported": False, "extension_enabled": False}, "EXTENSION_UNSUPPORTED"),
    ({"extension_enabled": False}, "EXTENSION_NOT_ENABLED"),
    ({"feature_supported": None}, "FEATURE_NOT_QUERIED"),
    ({"feature_supported": False, "feature_enabled": False, "session_inline_flag": False}, "FEATURE_UNSUPPORTED"),
    ({"feature_enabled": False, "session_inline_flag": False}, "FEATURE_NOT_ENABLED"),
    ({"feature_enabled": False}, "FLAG_REQUIRES_ENABLED_FEATURE"),
    ({"session_inline_flag": False}, "INLINE_SESSION_FLAG_MISSING"),
    ({"explicit_begin_query": True}, "EXPLICIT_QUERY_FORBIDDEN_IN_INLINE_SCOPE"),
    ({"target_slot_available": None}, "INLINE_QUERY_SLOT_STATE_UNKNOWN"),
    ({"queue_status_support": None}, "QUEUE_STATUS_SUPPORT_NOT_QUERIED"),
    ({"pool": None}, "NO_INLINE_QUERY_POOL"),
    ({"request_inline": False}, "UNEXPECTED_INLINE_QUERY_POOL"),
    ({"extension_supported": False, "extension_enabled": False, "feature_supported": None,
      "feature_enabled": False, "session_inline_flag": False, "pool": None,
      "request_inline": False}, "NO_INLINE_QUERY_REQUESTED"),
])
def test_decision_states_distinguish_unobserved_unsupported_and_no_request(diff, expected):
    observed = assess(**(facts() | diff))
    assert observed["status"] == expected
    assert observed["runtime_execution"] == "NOT_RUN"
    assert observed["vuids"] == (
        ["VUID-VkVideoSessionCreateInfoKHR-flags-08371"] if expected == "FLAG_REQUIRES_ENABLED_FEATURE" else []
    )


@pytest.mark.parametrize("bad", [
    {"query_count": True}, {"query_count": 1 << 32}, {"first_query": -1},
    {"target_slot_available": 0}, {"feature_supported": "false"}, {"pool": {}},
    {"session_profile": {"id": "not a complete profile"}},
])
def test_invalid_input_does_not_produce_a_positive_gate(bad):
    with pytest.raises(ValueError):
        assess(**(facts() | bad))


def test_a_separately_admissible_encode_feedback_pool_is_not_a_decode_pool():
    source = facts("encode")
    source["pool"]["type"] = ENCODE_FEEDBACK
    assert assess(**source)["status"] == "INLINE_QUERY_METADATA_ADMISSIBLE"
    decode = facts()
    decode["pool"] = source["pool"]
    assert assess(**decode)["vuids"] == [
        "VUID-vkCmdDecodeVideoKHR-queryType-08367",
        "VUID-vkCmdDecodeVideoKHR-queryPool-08368",
    ]


@pytest.mark.parametrize("pool_chroma", [0, 1, 4, 0x15])
def test_monochrome_ignores_the_chroma_depth_field(pool_chroma):
    plan = facts()
    plan["session_profile"].update(chroma_subsampling=1, chroma_bit_depth=0)
    plan["pool"]["profile"] = copy.deepcopy(plan["session_profile"])
    plan["pool"]["profile"]["chroma_bit_depth"] = pool_chroma
    original = copy.deepcopy(plan)
    assert assess(**plan)["status"] == "INLINE_QUERY_METADATA_ADMISSIBLE"
    assert plan == original


def test_color_profile_chroma_bit_depth_still_participates_in_compatibility():
    plan = facts()
    plan["pool"]["profile"]["chroma_bit_depth"] = 4
    assert assess(**plan)["vuids"] == ["VUID-vkCmdDecodeVideoKHR-queryPool-08368"]


def test_monochrome_ignored_semantics_do_not_admit_unregistered_flag_bits():
    plan = facts()
    plan["session_profile"]["chroma_subsampling"] = 1
    plan["pool"]["profile"] = copy.deepcopy(plan["session_profile"])
    plan["pool"]["profile"]["chroma_bit_depth"] = 0xFFFFFFFF
    with pytest.raises(ValueError, match="unregistered Vulkan flag bits"):
        assess(**plan)
    plan["pool"]["profile"]["chroma_bit_depth"] = 4
    plan["target_slot_available"] = None
    assert assess(**plan)["status"] == "INLINE_QUERY_SLOT_STATE_UNKNOWN"
