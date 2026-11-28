"""Bounded, offline Vulkan 1.4.368 maintenance1 inline-query admission.

One decode/encode operation, valid ordinary (non-protected) query-pool handle,
and caller-normalized complete profiles. No Vulkan calls or hardware claims.
Caller still owns queue/session creation, pool synchronization and result use.
"""
import json

STATUS_ONLY = "VK_QUERY_TYPE_RESULT_STATUS_ONLY_KHR"
ENCODE_FEEDBACK = "VK_QUERY_TYPE_VIDEO_ENCODE_FEEDBACK_KHR"
U32_MAX = 2**32 - 1
MONOCHROME = 1  # VK_VIDEO_CHROMA_SUBSAMPLING_MONOCHROME_BIT_KHR
# Registered bits in the frozen Vulkan 1.4.368 scope.
CHROMA_SUBSAMPLINGS = 0x0F
COMPONENT_DEPTHS = 0x15
PROFILE_FIELDS = {
    "codec_operation", "chroma_subsampling", "luma_bit_depth", "chroma_bit_depth", "profile_chain"
}
COMMAND_VUIDS = {
    "decode": (
        "VUID-vkCmdDecodeVideoKHR-pNext-08365",
        "VUID-vkCmdDecodeVideoKHR-pNext-08366",
        "VUID-vkCmdDecodeVideoKHR-queryType-08367",
        "VUID-vkCmdDecodeVideoKHR-queryPool-08368",
        "VUID-vkCmdDecodeVideoKHR-queryType-08369",
    ),
    "encode": (
        "VUID-vkCmdEncodeVideoKHR-pNext-08360",
        "VUID-vkCmdEncodeVideoKHR-pNext-08361",
        "VUID-vkCmdEncodeVideoKHR-queryType-08362",
        "VUID-vkCmdEncodeVideoKHR-queryPool-08363",
        "VUID-vkCmdEncodeVideoKHR-queryType-08364",
    ),
}


def result(status, *vuids):
    return {
        "status": status,
        "vuids": list(vuids),
        "evidence": "CALLER_DECLARED_OFFLINE_ONLY",
        "runtime_execution": "NOT_RUN",
    }


def boolean(value, name, allow_unknown=False):
    if type(value) is not bool and not (value is None and allow_unknown):
        raise ValueError(f"{name} must be boolean" + (" or unknown" if allow_unknown else ""))


def uint32(value, name):
    if type(value) is not int or not 0 <= value <= U32_MAX:
        raise ValueError(f"{name} must be uint32")


def canonical_profile(profile, direction):
    if type(profile) is not dict or set(profile) != PROFILE_FIELDS:
        raise ValueError("complete normalized profile fields required")
    codec = profile["codec_operation"]
    if type(codec) is not str or not codec.startswith(f"VK_VIDEO_CODEC_OPERATION_{direction.upper()}_"):
        raise ValueError("profile codec operation must match command direction")
    for key in ("chroma_subsampling", "luma_bit_depth", "chroma_bit_depth"):
        uint32(profile[key], key)
        valid_bits = CHROMA_SUBSAMPLINGS if key == "chroma_subsampling" else COMPONENT_DEPTHS
        if profile[key] & ~valid_bits:
            raise ValueError(f"{key} contains unregistered Vulkan flag bits")
        if key == "chroma_bit_depth" and profile["chroma_subsampling"] == MONOCHROME:
            continue
        if not profile[key] or (profile[key] & (profile[key] - 1)):
            raise ValueError(f"{key} must name a single profile bit")
    chain = profile["profile_chain"]
    if type(chain) is not dict or not chain:
        raise ValueError("normalized codec-specific profile chain required")
    # Dictionary content represents complete pNext semantics, not pointer identity
    # or a caller-chosen profile label. Distinguish JSON booleans from integers.
    normalized = dict(profile)
    if normalized["chroma_subsampling"] == MONOCHROME:
        normalized["chroma_bit_depth"] = 0  # Vulkan ignores it for monochrome profiles.
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), allow_nan=False)


def assess(*, direction, extension_supported, extension_enabled, feature_supported,
           feature_enabled, session_inline_flag, request_inline, explicit_begin_query,
           session_profile=None, pool=None, first_query=0, query_count=0,
           target_slot_available=None, queue_status_support=None):
    """Preflight one application plan, not a general VkCommandBuffer validator.

    `pool` is non-null only for a known valid pool. `target_slot_available`
    describes the selected slot at ordered command execution, not a host poll
    or permission to reset an in-flight pool. This scope does not validate
    queue/session/DPB/codec creation, feedback flags, or consumption of results.
    """
    if type(direction) is not str or direction not in COMMAND_VUIDS:
        raise ValueError("direction must be decode or encode")
    for name, value in (("extension_supported", extension_supported),
                        ("feature_supported", feature_supported),
                        ("target_slot_available", target_slot_available),
                        ("queue_status_support", queue_status_support)):
        boolean(value, name, allow_unknown=True)
    for name, value in (("extension_enabled", extension_enabled),
                        ("feature_enabled", feature_enabled),
                        ("session_inline_flag", session_inline_flag),
                        ("request_inline", request_inline),
                        ("explicit_begin_query", explicit_begin_query)):
        boolean(value, name)
    if session_inline_flag and not feature_enabled:
        return result("FLAG_REQUIRES_ENABLED_FEATURE", "VUID-VkVideoSessionCreateInfoKHR-flags-08371")
    if session_inline_flag and explicit_begin_query:
        return result("EXPLICIT_QUERY_FORBIDDEN_IN_INLINE_SCOPE")
    if not request_inline:
        if pool is not None:
            return result("UNEXPECTED_INLINE_QUERY_POOL")
        return result("NO_INLINE_QUERY_REQUESTED")
    for found, enabled, kind in (
        (extension_supported, extension_enabled, "EXTENSION"),
        (feature_supported, feature_enabled, "FEATURE"),
    ):
        if found is None:
            return result(f"{kind}_NOT_QUERIED")
        if not found:
            return result(f"{kind}_UNSUPPORTED")
        if not enabled:
            return result(f"{kind}_NOT_ENABLED")
    if not session_inline_flag:
        return result("INLINE_SESSION_FLAG_MISSING")
    if pool is None:
        return result("NO_INLINE_QUERY_POOL")
    if type(pool) is not dict or set(pool) != {"type", "size", "profile"}:
        raise ValueError("pool needs a type, size and complete creation profile")
    size = pool["size"]
    for name, value in (("pool size", size), ("firstQuery", first_query), ("queryCount", query_count)):
        uint32(value, name)
    if not size:
        raise ValueError("pool size must be positive")
    count_vuid, availability_vuid, type_vuid, profile_vuid, queue_vuid = COMMAND_VUIDS[direction]
    violations = []
    if first_query >= size:
        violations.append("VUID-VkVideoInlineQueryInfoKHR-queryPool-08372")
    if first_query + query_count > size:
        violations.append("VUID-VkVideoInlineQueryInfoKHR-queryPool-08373")
    if query_count != 1:
        violations.append(count_vuid)
    if pool["type"] not in ((STATUS_ONLY,) if direction == "decode" else (STATUS_ONLY, ENCODE_FEEDBACK)):
        violations.append(type_vuid)
    # The pool may be valid for another codec or for the opposite operation;
    # canonicalize it separately and classify an actual difference as a VUID.
    profile = canonical_profile(session_profile, direction)
    other = pool["profile"]
    codec = other.get("codec_operation") if isinstance(other, dict) else None
    is_encode_pool = isinstance(codec, str) and codec.startswith("VK_VIDEO_CODEC_OPERATION_ENCODE_")
    other_direction = "encode" if is_encode_pool else "decode"
    if profile != canonical_profile(other, other_direction):
        violations.append(profile_vuid)
    if query_count == 1 and first_query < size and target_slot_available is True:
        violations.append(availability_vuid)
    if pool["type"] == STATUS_ONLY and queue_status_support is False:
        violations.append(queue_vuid)
    if violations:
        return result("INLINE_QUERY_CONTRACT_REJECTED", *violations)
    if target_slot_available is None:
        return result("INLINE_QUERY_SLOT_STATE_UNKNOWN")
    if pool["type"] == STATUS_ONLY and queue_status_support is None:
        return result("QUEUE_STATUS_SUPPORT_NOT_QUERIED")
    return result("INLINE_QUERY_METADATA_ADMISSIBLE")
