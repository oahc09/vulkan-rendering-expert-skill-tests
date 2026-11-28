// SPDX-License-Identifier: MIT
// Syntax-only probe. Select the reviewed legacy build explicitly.
#include <vulkan/vulkan.h>

#if defined(V21_LEGACY_APPLE_BUILD)
#if !defined(VK_KHR_portability_subset)
#error "This legacy build needs headers with VK_KHR_portability_subset declarations"
#endif
VkPhysicalDevicePortabilitySubsetFeaturesKHR subset_features{
    VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PORTABILITY_SUBSET_FEATURES_KHR};
const char *device_extension = VK_KHR_PORTABILITY_SUBSET_EXTENSION_NAME;
#endif

static_assert(VK_INSTANCE_CREATE_ENUMERATE_PORTABILITY_BIT_KHR != 0,
              "The enumeration flag must be available in this build");
const char *instance_extension = VK_KHR_PORTABILITY_ENUMERATION_EXTENSION_NAME;
