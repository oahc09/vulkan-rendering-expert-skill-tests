// SPDX-License-Identifier: MIT
#pragma once

#include <algorithm>
#include <cstdint>
#include <optional>
#include <vector>

enum class VisibilityResult { Match, Different, Duplicate, Insufficient };

// Diagnostic membership for one serialized opaque run. Overflow is permitted
// only as an incomplete result; every retained ID must still be expected.
inline VisibilityResult compareOpaqueIds(std::vector<uint32_t> &observed,
                                         std::vector<uint32_t> expected,
                                         bool overflow) {
  std::sort(observed.begin(), observed.end());
  std::sort(expected.begin(), expected.end());
  if (std::adjacent_find(observed.begin(), observed.end()) != observed.end())
    return VisibilityResult::Duplicate;
  if (!std::includes(expected.begin(), expected.end(), observed.begin(),
                     observed.end()))
    return VisibilityResult::Different;
  if (overflow)
    return VisibilityResult::Insufficient;
  return observed == expected ? VisibilityResult::Match
                              : VisibilityResult::Different;
}

// An external readback must establish its own generation and ordering scope.
inline VisibilityResult compareScopedVisibility(
    std::vector<uint32_t> observed, const std::vector<uint32_t> &expected,
    std::optional<uint64_t> observedGeneration,
    std::optional<uint64_t> expectedGeneration, bool opaqueOrderIndependent) {
  if (!observedGeneration || !expectedGeneration || !opaqueOrderIndependent)
    return VisibilityResult::Insufficient;
  if (observedGeneration != expectedGeneration)
    return VisibilityResult::Different;
  return compareOpaqueIds(observed, expected, false);
}
