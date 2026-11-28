/* SPDX-License-Identifier: MIT
 * The normal build runs the valid A -> B -> A sequence on NVIDIA.
 * V21_MOCK_NEGATIVE can run a missing-dependency control only on Mock ICD.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vulkan/vulkan.h>

static const char *phase = "setup";
static unsigned errors;

static VKAPI_ATTR VkBool32 VKAPI_CALL monitor(
    VkDebugUtilsMessageSeverityFlagBitsEXT severity, VkDebugUtilsMessageTypeFlagsEXT type,
    const VkDebugUtilsMessengerCallbackDataEXT *message, void *data) {
    (void)severity;
    (void)type;
    (void)data;
    ++errors;
    fprintf(stderr, "VVL phase=%s id=%s\n", phase,
            message->pMessageIdName ? message->pMessageIdName : "unknown");
    return VK_TRUE;
}

static VkResult submit(VkQueue queue, VkCommandBuffer command, VkSemaphore wait, VkSemaphore signal) {
    const VkPipelineStageFlags transfer = VK_PIPELINE_STAGE_TRANSFER_BIT;
#ifndef V21_MOCK_NEGATIVE
    const uint64_t one = 1;
    VkTimelineSemaphoreSubmitInfo timeline = {
        .sType = VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO,
        .waitSemaphoreValueCount = wait ? 1 : 0, .pWaitSemaphoreValues = &one,
        .signalSemaphoreValueCount = signal ? 1 : 0, .pSignalSemaphoreValues = &one,
    };
#endif
    VkSubmitInfo submission = {
        .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO,
#ifndef V21_MOCK_NEGATIVE
        .pNext = &timeline,
#endif
        .waitSemaphoreCount = wait ? 1 : 0, .pWaitSemaphores = &wait, .pWaitDstStageMask = &transfer,
        .commandBufferCount = 1, .pCommandBuffers = &command,
        .signalSemaphoreCount = signal ? 1 : 0, .pSignalSemaphores = &signal,
    };
    return vkQueueSubmit(queue, 1, &submission, VK_NULL_HANDLE);
}

#define CHECK(call) do { \
    VkResult value = (call); \
    if (value != VK_SUCCESS) { \
        fprintf(stderr, "API %s result=%d\n", #call, value); \
        goto cleanup; \
    } \
} while (0)

int main(void) {
    const char *layer = "VK_LAYER_KHRONOS_validation";
    const char *extensions[] = {VK_EXT_DEBUG_UTILS_EXTENSION_NAME, VK_EXT_VALIDATION_FEATURES_EXTENSION_NAME};
    const VkValidationFeatureEnableEXT sync = VK_VALIDATION_FEATURE_ENABLE_SYNCHRONIZATION_VALIDATION_EXT;
    VkInstance instance = VK_NULL_HANDLE;
    VkDebugUtilsMessengerEXT messenger = VK_NULL_HANDLE;
    PFN_vkDestroyDebugUtilsMessengerEXT destroy = NULL;
    VkPhysicalDevice *devices = NULL;
    VkQueueFamilyProperties *families = NULL;
    VkDevice device = VK_NULL_HANDLE;
    VkBuffer buffer = VK_NULL_HANDLE;
    VkDeviceMemory memory = VK_NULL_HANDLE;
    VkCommandPool pool = VK_NULL_HANDLE;
    VkSemaphore a = VK_NULL_HANDLE, b = VK_NULL_HANDLE;
    int rc = 2;
    VkResult last = VK_NOT_READY;
    uint32_t count = 0, family = UINT32_MAX, queue_count = 0;

    VkApplicationInfo app = {.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO, .apiVersion = VK_API_VERSION_1_2};
    VkDebugUtilsMessengerCreateInfoEXT debug = {
        .sType = VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT,
        .messageSeverity = VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT,
        .messageType = VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT, .pfnUserCallback = monitor,
    };
    VkValidationFeaturesEXT validation = {
        .sType = VK_STRUCTURE_TYPE_VALIDATION_FEATURES_EXT, .pNext = &debug,
        .enabledValidationFeatureCount = 1, .pEnabledValidationFeatures = &sync,
    };
    VkInstanceCreateInfo ci = {
        .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pNext = &validation, .pApplicationInfo = &app,
        .enabledLayerCount = 1, .ppEnabledLayerNames = &layer,
        .enabledExtensionCount = 2, .ppEnabledExtensionNames = extensions,
    };
    CHECK(vkCreateInstance(&ci, NULL, &instance));
    PFN_vkCreateDebugUtilsMessengerEXT create = (PFN_vkCreateDebugUtilsMessengerEXT)
        vkGetInstanceProcAddr(instance, "vkCreateDebugUtilsMessengerEXT");
    destroy = (PFN_vkDestroyDebugUtilsMessengerEXT)
        vkGetInstanceProcAddr(instance, "vkDestroyDebugUtilsMessengerEXT");
    if (!create || !destroy) goto cleanup;
    CHECK(create(instance, &debug, NULL, &messenger));

    CHECK(vkEnumeratePhysicalDevices(instance, &count, NULL));
    if (!count) goto cleanup;
    devices = calloc(count, sizeof(*devices));
    if (!devices) goto cleanup;
    CHECK(vkEnumeratePhysicalDevices(instance, &count, devices));
    VkPhysicalDevice physical = VK_NULL_HANDLE;
    for (uint32_t i = 0; i < count; ++i) {
        VkPhysicalDeviceProperties properties;
        vkGetPhysicalDeviceProperties(devices[i], &properties);
#ifdef V21_MOCK_NEGATIVE
        if (count != 1 || properties.vendorID != 0xba5eba11u ||
            strcmp(properties.deviceName, "Vulkan Mock Device") != 0) goto cleanup;
        const int selected = 1;
#else
        const int selected = properties.vendorID == 0x10de &&
                             properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU;
#endif
        if (selected) {
            if (physical || properties.apiVersion < VK_API_VERSION_1_2) goto cleanup;
            physical = devices[i];
            fprintf(stderr, "IDENTITY vendor=%u device=%u driver=%u api=%u\n",
                    properties.vendorID, properties.deviceID, properties.driverVersion, properties.apiVersion);
        }
    }
    if (!physical) goto cleanup;
    vkGetPhysicalDeviceQueueFamilyProperties(physical, &count, NULL);
    families = calloc(count, sizeof(*families));
    if (!families) goto cleanup;
    vkGetPhysicalDeviceQueueFamilyProperties(physical, &count, families);
    for (uint32_t i = 0; i < count; ++i) {
        if (families[i].queueCount >= 2 && (families[i].queueFlags & VK_QUEUE_TRANSFER_BIT)) {
            family = i;
            queue_count = families[i].queueCount;
            break;
        }
    }
    if (family == UINT32_MAX) {
        rc = 77;
        goto cleanup;
    }
#ifndef V21_MOCK_NEGATIVE
    VkPhysicalDeviceTimelineSemaphoreFeatures timeline = {
        .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_TIMELINE_SEMAPHORE_FEATURES,
    };
    VkPhysicalDeviceFeatures2 support = {
        .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2, .pNext = &timeline,
    };
    vkGetPhysicalDeviceFeatures2(physical, &support);
    if (!timeline.timelineSemaphore) {
        rc = 77;
        goto cleanup;
    }
#endif

    const float priorities[] = {1.0f, 1.0f};
    VkDeviceQueueCreateInfo queues = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
        .queueFamilyIndex = family, .queueCount = 2, .pQueuePriorities = priorities,
    };
    VkDeviceCreateInfo dc = {
        .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
#ifndef V21_MOCK_NEGATIVE
        .pNext = &timeline,
#endif
        .queueCreateInfoCount = 1, .pQueueCreateInfos = &queues,
    };
    CHECK(vkCreateDevice(physical, &dc, NULL, &device));
    VkQueue queue_a, queue_b;
    vkGetDeviceQueue(device, family, 0, &queue_a);
    vkGetDeviceQueue(device, family, 1, &queue_b);
    VkBufferCreateInfo bc = {
        .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, .size = 256,
        .usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT, .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
    };
    CHECK(vkCreateBuffer(device, &bc, NULL, &buffer));
    VkMemoryRequirements mr;
    vkGetBufferMemoryRequirements(device, buffer, &mr);
    uint32_t memory_type = 0;
    if (!mr.memoryTypeBits) goto cleanup;
    while (!(mr.memoryTypeBits & (1u << memory_type))) ++memory_type;
    VkMemoryAllocateInfo ai = {
        .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, .allocationSize = mr.size, .memoryTypeIndex = memory_type,
    };
    CHECK(vkAllocateMemory(device, &ai, NULL, &memory));
    CHECK(vkBindBufferMemory(device, buffer, memory, 0));
    VkSemaphoreCreateInfo sc = {.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
#ifndef V21_MOCK_NEGATIVE
    VkSemaphoreTypeCreateInfo type = {
        .sType = VK_STRUCTURE_TYPE_SEMAPHORE_TYPE_CREATE_INFO, .semaphoreType = VK_SEMAPHORE_TYPE_TIMELINE,
    };
    sc.pNext = &type;
#endif
    CHECK(vkCreateSemaphore(device, &sc, NULL, &a));
    CHECK(vkCreateSemaphore(device, &sc, NULL, &b));
    VkCommandPoolCreateInfo pc = {.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO, .queueFamilyIndex = family};
    CHECK(vkCreateCommandPool(device, &pc, NULL, &pool));
    VkCommandBufferAllocateInfo ca = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO, .commandPool = pool,
        .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1,
    };
    VkCommandBuffer command;
    CHECK(vkAllocateCommandBuffers(device, &ca, &command));
    VkCommandBufferBeginInfo begin = {
        .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO, .flags = VK_COMMAND_BUFFER_USAGE_SIMULTANEOUS_USE_BIT,
    };
    CHECK(vkBeginCommandBuffer(command, &begin));
    vkCmdFillBuffer(command, buffer, 0, 256, 0x42);
    CHECK(vkEndCommandBuffer(command));
    phase = "a-first";
    CHECK(submit(queue_a, command, VK_NULL_HANDLE, a));
#ifdef V21_MOCK_NEGATIVE
    phase = "b-missing-wait";
    last = submit(queue_b, command, VK_NULL_HANDLE, b);
    rc = last == VK_ERROR_VALIDATION_FAILED_EXT ? 3 : 2;
#else
    phase = "b";
    CHECK(submit(queue_b, command, a, b));
    phase = "host-wait";
    const uint64_t one = 1;
    VkSemaphoreWaitInfo wait = {
        .sType = VK_STRUCTURE_TYPE_SEMAPHORE_WAIT_INFO,
        .semaphoreCount = 1, .pSemaphores = &b, .pValues = &one,
    };
    CHECK(vkWaitSemaphores(device, &wait, 10000000000ull));
    phase = "a-final";
    last = submit(queue_a, command, b, VK_NULL_HANDLE);
    rc = last == VK_SUCCESS ? 0 : last == VK_ERROR_VALIDATION_FAILED_EXT ? 3 : 2;
#endif

cleanup:
    phase = "cleanup";
    free(devices);
    free(families);
    if (device) {
        if (vkDeviceWaitIdle(device) != VK_SUCCESS) rc = 2;
        if (pool) vkDestroyCommandPool(device, pool, NULL);
        if (a) vkDestroySemaphore(device, a, NULL);
        if (b) vkDestroySemaphore(device, b, NULL);
        if (buffer) vkDestroyBuffer(device, buffer, NULL);
        if (memory) vkFreeMemory(device, memory, NULL);
        vkDestroyDevice(device, NULL);
    }
    if (messenger) destroy(instance, messenger, NULL);
    if (instance) vkDestroyInstance(instance, NULL);
    if (rc == 0 && errors) rc = 2;
    printf("{\"queue_family\":%u,\"queue_count\":%u,\"final_submit\":%d,\"errors\":%u,\"exit_code\":%d}\n",
           family, queue_count, last, errors, rc);
    return rc;
}
