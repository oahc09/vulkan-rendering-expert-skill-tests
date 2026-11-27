#pragma once
#include "common/helpers.h"
namespace vkb { class Device { public: VkDevice get_handle() const { return reinterpret_cast<VkDevice>(uintptr_t(41)); } }; }
