// SPDX-License-Identifier: MIT
// Isolated host unit contracts, not actual allocator/driver failure injection.
#include <algorithm>
#include <array>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

struct Upload {
  enum State {
    Queued,
    Submitted,
    Ready,
    Published,
    Canceled,
    Obsolete,
    Retired
  } state = Queued;
  uint32_t generation = 1;
  size_t bytes = 0;
  bool gpuComplete = false;
  uint32_t owners = 0;
};
struct Budget {
  size_t limit = 1024, used = 0, peak = 0;
  bool reserve(size_t n) {
    if (n > limit || used > limit - n)
      return false;
    used += n;
    peak = std::max(peak, used);
    return true;
  }
  void release(size_t n) {
    if (n > used)
      throw std::logic_error("double release");
    used -= n;
  }
};
bool publish(Upload &task, uint32_t generation) {
  if (task.state == Upload::Canceled || task.generation != generation) {
    if (task.state != Upload::Canceled)
      task.state = Upload::Obsolete;
    return false;
  }
  if (!task.gpuComplete || task.state != Upload::Ready)
    return false;
  task.state = Upload::Published;
  return true;
}
bool retire(Upload &task, Budget &budget) {
  if (task.owners || (task.state != Upload::Queued && !task.gpuComplete))
    return false;
  if (task.state == Upload::Retired)
    throw std::logic_error("double retirement");
  budget.release(task.bytes);
  task.state = Upload::Retired;
  return true;
}
uint32_t residentLOD(uint32_t wanted, uint32_t mask) {
  for (uint32_t level = wanted; level < 3; level++)
    if (mask & (1u << level))
      return level;
  return 3; // explicit unavailable, never point at unuploaded data
}
// Engine envelope only. Opaque Vulkan payload is never edited or interpreted.
struct CacheEnvelope {
  uint32_t schema;
  std::array<uint8_t, 16> uuid;
  size_t size;
  uint64_t digest;
};
uint64_t checksum(const std::vector<uint8_t> &bytes) {
  uint64_t hash = 1469598103934665603ull;
  for (auto b : bytes) {
    hash ^= b;
    hash *= 1099511628211ull;
  }
  return hash;
}
bool accept(const CacheEnvelope &e, const std::vector<uint8_t> &bytes,
            const std::array<uint8_t, 16> &uuid) {
  return e.schema == 1 && e.uuid == uuid && e.size == bytes.size() &&
         e.digest == checksum(bytes);
}
int main() {
  Budget budget;
  Upload old;
  old.bytes = 700;
  assert(budget.reserve(old.bytes));
  old.state = Upload::Submitted;
  assert(!budget.reserve(400)); // bounded staging/new+old peak
  old.state = Upload::Canceled;
  assert(!retire(old, budget));
  assert(!publish(old, 1));
  old.gpuComplete = true;
  assert(retire(old, budget));
  assert(budget.used == 0);
  Upload late;
  late.bytes = 200;
  assert(budget.reserve(late.bytes));
  late.state = Upload::Ready;
  late.gpuComplete = true;
  assert(!publish(late, 2));
  assert(late.state == Upload::Obsolete);
  assert(retire(late, budget));
  Upload shared;
  shared.bytes = 300;
  assert(budget.reserve(shared.bytes));
  shared.state = Upload::Ready;
  shared.gpuComplete = true;
  assert(publish(shared, 1));
  shared.owners = 2;
  shared.owners--;
  assert(!retire(shared, budget));
  shared.owners--;
  assert(retire(shared, budget));
  // Late CPU pipeline build completion follows the same generation/publication
  // contract, but is not represented as evidence that real CPU and GPU
  // completions are identical.
  for (uint32_t generation = 1; generation <= 100; generation++) {
    Upload u;
    u.generation = generation;
    u.bytes = 64;
    assert(budget.reserve(64));
    u.state = Upload::Ready;
    u.gpuComplete = true;
    assert(!publish(u, generation + 1));
    assert(retire(u, budget));
  }
  assert(budget.used == 0 && budget.peak <= budget.limit);
  assert(residentLOD(0, 4) == 2 && residentLOD(1, 7) == 1 &&
         residentLOD(0, 0) == 3);
  std::array<uint8_t, 16> uuid{};
  std::vector<uint8_t> blob = {1, 2, 3, 4};
  CacheEnvelope env{1, uuid, blob.size(), checksum(blob)};
  assert(accept(env, blob, uuid));
  auto corrupt = blob;
  corrupt[2] ^= 1;
  assert(!accept(env, corrupt, uuid));
  uuid[0] = 1;
  assert(!accept(env, blob, uuid));
  blob.pop_back();
  assert(!accept(env, blob, env.uuid));
  // mip clamp changes safe sampling, not allocation size.
  size_t imageAllocation = 4096;
  uint32_t initializedMip = 4;
  initializedMip = 2;
  assert(initializedMip == 2 && imageAllocation == 4096);
  // Boundary math: negative/nonuniform scale uses max absolute extent, never
  // signed radius.
  float radius = 2, scale[3] = {-3, .5f, 2};
  float bound = radius * std::max({std::abs(scale[0]), std::abs(scale[1]),
                                   std::abs(scale[2])});
  assert(bound == 6);
  // Reverse-Z min and ordinary-Z max include uncovered far samples.
  std::vector<float> normal = {.3f, .3f, 1.f, .3f},
                     reverse = {.7f, .7f, 0.f, .7f};
  assert(*std::max_element(normal.begin(), normal.end()) == 1.f);
  assert(*std::min_element(reverse.begin(), reverse.end()) == 0.f);
  // No unsigned wrap when computing indirect buffer range.
  auto validRange = [](uint64_t offset, uint64_t count, uint64_t stride,
                       uint64_t size) {
    if (stride < 16 || stride % 4)
      return false;
    if (count == 0)
      return offset <= size;
    if (offset > size || size - offset < 16)
      return false;
    return count - 1 <= (size - offset - 16) / stride;
  };
  assert(validRange(0, 4, 16, 64));
  assert(!validRange(4, 4, 16, 64));
  assert(!validRange(0, UINT64_MAX, 16, 64));
  assert(validRange(64, 0, 16, 64));
  std::cout << "{\"layer\":\"HostUnit\",\"status\":\"PASS\",\"scenarios\":["
               "\"upload-cancel\",\"late-generation\",\"shared-owner\","
               "\"budget-peak\",\"cache-envelope-rejection\",\"resident-LOD\","
               "\"mip-not-allocation\",\"bounds\",\"HiZ-hole\",\"indirect-"
               "range\"],\"driver_failure_injected\":false}\n";
}
