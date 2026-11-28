"""Fixed expected outcomes for ordinary non-sparse UBO descriptor updates."""
from tools.descriptor19 import WHOLE, check


def test_whole_remainder_and_explicit_range_equivalence():
    facts = dict(buffer_size=1024, offset=256, max_range=768, alignment=256,
                 bound=True, uniform_usage=True, update_safe=True)
    whole = check(range_bytes=WHOLE, **facts)
    remainder = check(range_bytes=768, **facts)
    shorter = check(range_bytes=767, **facts)
    assert whole == remainder
    assert (whole["status"], whole["effective_range"]) == ("WITHIN_CHECKED_SCOPE", 768)
    assert (shorter["status"], shorter["effective_range"]) == ("WITHIN_CHECKED_SCOPE", 767)

    misaligned = check(range_bytes=WHOLE, **(facts | {"offset": 257}))
    overflow = check(range_bytes=769, **facts)
    limited = check(range_bytes=WHOLE, **(facts | {"max_range": 767}))
    assert misaligned["vuids"] == ["VUID-VkWriteDescriptorSet-descriptorType-00327"]
    assert "VUID-VkDescriptorBufferInfo-range-00342" in overflow["vuids"]
    assert limited["vuids"] == ["VUID-VkWriteDescriptorSet-descriptorType-00332"]
    assert all(row["status"] == "REJECTED" for row in (misaligned, overflow, limited))
    assert check(range_bytes=WHOLE, **(facts | {"max_range": None}))["status"] == "UNKNOWN"
