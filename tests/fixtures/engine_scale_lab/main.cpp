// SPDX-License-Identifier: MIT
// Original minimal offscreen integration fixture. No window/engine/assets
// required.
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>
#include <vulkan/vulkan.h>
#define VK(call)                                                               \
  do {                                                                         \
    VkResult checked_result_ = (call);                                         \
    if (checked_result_ != VK_SUCCESS)                                         \
      throw std::runtime_error(std::string(#call) + ": " +                     \
                               std::to_string(checked_result_));               \
  } while (0)
struct Object {
  float sphere[4];
  uint32_t meta[4];
};
struct Push {
  uint32_t n, capacity, mode, flags, width, height, level, tick;
  float viewX, zoom;
  uint32_t base, unused;
};
static_assert(sizeof(Object) == 32 && offsetof(Object, meta) == 16,
              "std430 ABI");
static_assert(sizeof(Push) == 48 && offsetof(Push, viewX) == 32, "push ABI");
static_assert(sizeof(VkDrawIndirectCommand) == 16 &&
                  offsetof(VkDrawIndexedIndirectCommand, vertexOffset) == 12,
              "indirect ABI");
struct Buffer {
  VkBuffer buffer{};
  VkDeviceMemory memory{};
  void *map{};
  VkDeviceSize size{};
};
struct Image {
  VkImage image{};
  VkDeviceMemory memory{};
  VkImageView view{};
};
static uint32_t validationErrors = 0;
static std::string artifactDirectory;
static uint32_t artifactSequence = 0;
VKAPI_ATTR VkBool32 VKAPI_CALL
debug(VkDebugUtilsMessageSeverityFlagBitsEXT severity,
      VkDebugUtilsMessageTypeFlagsEXT,
      const VkDebugUtilsMessengerCallbackDataEXT *data, void *) {
  if (severity >= VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT)
    validationErrors++;
  std::cerr << "VALIDATION: " << data->pMessage << "\n";
  return VK_FALSE;
}
struct Vulkan {
  VkInstance instance{};
  VkDebugUtilsMessengerEXT messenger{};
  VkPhysicalDevice physical{};
  VkDevice device{};
  VkQueue queue{};
  uint32_t family{};
  VkPhysicalDeviceProperties properties{};
  VkPhysicalDeviceMemoryProperties mem{};
  bool firstInstance{}, mdi{}, countEnabled{}, validation{};
  VkCommandPool pool{};
  VkCommandBuffer cb{};
  VkFence fence{};
  VkDescriptorSetLayout setLayout{};
  VkPipelineLayout layout{};
  VkDescriptorPool descriptors{};
  VkDescriptorSet set{}, swapSet{};
  VkRenderPass clearPass{}, loadPass{};
  VkFramebuffer framebuffer{};
  VkSampler sampler{};
  Image color, depth;
  std::vector<Buffer> buffers;
  std::vector<VkPipeline> pipelines;
  VkPipeline update{}, hiz{}, cull{}, finalize{}, graphics{}, additive{},
      alpha{}, graphicsReverse{}, additiveReverse{}, alphaReverse{};
  VkQueryPool queries{};
  VkPipelineCache pipelineCache{};
  bool timestamps = false;
  uint32_t timestampBits = 0;
  uint32_t width = 65, height = 49, levels = 1, n;
  uint64_t allocated = 0;
  std::string shaders;
  Vulkan(uint32_t size, std::string shaderDir, bool forceLow)
      : n(size), shaders(shaderDir) {
    VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
    app.pApplicationName = "Engine Scale Lab";
    app.apiVersion = VK_API_VERSION_1_2;
    VkInstanceCreateInfo info{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
    info.pApplicationInfo = &app;
    uint32_t layerCount = 0;
    VK(vkEnumerateInstanceLayerProperties(&layerCount, nullptr));
    std::vector<VkLayerProperties> layers(layerCount);
    VK(vkEnumerateInstanceLayerProperties(&layerCount, layers.data()));
    validation = std::any_of(layers.begin(), layers.end(), [](auto &l) {
      return std::string(l.layerName) == "VK_LAYER_KHRONOS_validation";
    });
    const char *layer = "VK_LAYER_KHRONOS_validation";
    const char *ext = "VK_EXT_debug_utils";
    VkDebugUtilsMessengerCreateInfoEXT di{
        VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT};
    di.messageSeverity = VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT |
                         VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT;
    di.messageType = 7;
    di.pfnUserCallback = debug;
    if (validation) {
      info.enabledLayerCount = 1;
      info.ppEnabledLayerNames = &layer;
      info.enabledExtensionCount = 1;
      info.ppEnabledExtensionNames = &ext;
      info.pNext = &di;
    }
    VK(vkCreateInstance(&info, nullptr, &instance));
    if (validation) {
      auto fn = (PFN_vkCreateDebugUtilsMessengerEXT)vkGetInstanceProcAddr(
          instance, "vkCreateDebugUtilsMessengerEXT");
      VK(fn(instance, &di, nullptr, &messenger));
    }
    uint32_t devices = 0;
    VK(vkEnumeratePhysicalDevices(instance, &devices, nullptr));
    if (!devices)
      throw std::runtime_error("BLOCKED: no Vulkan device");
    std::vector<VkPhysicalDevice> list(devices);
    VK(vkEnumeratePhysicalDevices(instance, &devices, list.data()));
    for (auto pd : list) {
      uint32_t num = 0;
      vkGetPhysicalDeviceQueueFamilyProperties(pd, &num, nullptr);
      std::vector<VkQueueFamilyProperties> qs(num);
      vkGetPhysicalDeviceQueueFamilyProperties(pd, &num, qs.data());
      for (uint32_t i = 0; i < num; i++)
        if ((qs[i].queueFlags & 3) == 3) {
          physical = pd;
          family = i;
          timestampBits = qs[i].timestampValidBits;
          break;
        }
      if (physical)
        break;
    }
    if (!physical)
      throw std::runtime_error("BLOCKED: no graphics+compute queue");
    vkGetPhysicalDeviceProperties(physical, &properties);
    vkGetPhysicalDeviceMemoryProperties(physical, &mem);
    timestamps =
        properties.limits.timestampComputeAndGraphics && timestampBits > 0;
    if (properties.apiVersion < VK_API_VERSION_1_2)
      throw std::runtime_error(
          "Fixture requires Vulkan1.2; engine baseline need not");
    VkPhysicalDeviceVulkan12Features f12{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES};
    VkPhysicalDeviceFeatures2 f2{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};
    f2.pNext = &f12;
    vkGetPhysicalDeviceFeatures2(physical, &f2);
    firstInstance = f2.features.drawIndirectFirstInstance && !forceLow;
    mdi = f2.features.multiDrawIndirect && !forceLow;
    countEnabled = f12.drawIndirectCount && firstInstance && !forceLow;
    VkPhysicalDeviceFeatures enabled{};
    enabled.drawIndirectFirstInstance = firstInstance;
    enabled.multiDrawIndirect = mdi;
    VkPhysicalDeviceVulkan12Features enabled12{
        VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES};
    enabled12.drawIndirectCount = countEnabled;
    float priority = 1;
    VkDeviceQueueCreateInfo qi{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
    qi.queueFamilyIndex = family;
    qi.queueCount = 1;
    qi.pQueuePriorities = &priority;
    VkDeviceCreateInfo dc{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
    dc.pNext = &enabled12;
    dc.pEnabledFeatures = &enabled;
    dc.queueCreateInfoCount = 1;
    dc.pQueueCreateInfos = &qi;
    VK(vkCreateDevice(physical, &dc, nullptr, &device));
    vkGetDeviceQueue(device, family, 0, &queue);
    if (properties.limits.maxPerStageDescriptorStorageBuffers < 7 ||
        properties.limits.maxDescriptorSetStorageBuffers < 7 ||
        properties.limits.maxPerStageResources < 8 ||
        properties.limits.maxComputeWorkGroupSize[0] < 64)
      throw std::runtime_error("BLOCKED: fixture descriptor/workgroup limits "
                               "unsupported; not an engine baseline");
    if ((n + 63) / 64 > properties.limits.maxComputeWorkGroupCount[0] ||
        64 > properties.limits.maxComputeWorkGroupInvocations)
      throw std::runtime_error("Scale exceeds compute limits");
    VkCommandPoolCreateInfo pc{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
    pc.queueFamilyIndex = family;
    pc.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    VK(vkCreateCommandPool(device, &pc, nullptr, &pool));
    VkCommandBufferAllocateInfo ca{
        VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
    ca.commandPool = pool;
    ca.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    ca.commandBufferCount = 1;
    VK(vkAllocateCommandBuffers(device, &ca, &cb));
    VkFenceCreateInfo fc{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
    VK(vkCreateFence(device, &fc, nullptr, &fence));
    uint32_t w = width, h = height;
    uint64_t pixels = uint64_t(w) * h;
    while (w > 1 || h > 1) {
      w = (w + 1) / 2;
      h = (h + 1) / 2;
      pixels += uint64_t(w) * h;
      levels++;
    }
    // Explicit allocation capacities, guarded extra command/id slots catch OOB
    // writes.
    buffers.push_back(buffer(uint64_t(n) * sizeof(Object),
                             VK_BUFFER_USAGE_STORAGE_BUFFER_BIT));
    buffers.push_back(buffer(uint64_t(n) * sizeof(Object),
                             VK_BUFFER_USAGE_STORAGE_BUFFER_BIT));
    buffers.push_back(
        buffer(uint64_t(n + 2) * 16, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT |
                                         VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT |
                                         VK_BUFFER_USAGE_TRANSFER_DST_BIT));
    buffers.push_back(buffer(16, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT |
                                     VK_BUFFER_USAGE_INDIRECT_BUFFER_BIT |
                                     VK_BUFFER_USAGE_TRANSFER_DST_BIT));
    buffers.push_back(
        buffer(uint64_t(n + 1) * 4, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT));
    buffers.push_back(buffer(pixels * 4, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT));
    buffers.push_back(buffer(
        uint64_t(n) * 4, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT)); // lods, binding7
    buffers.push_back(buffer(uint64_t(width) * height * 4,
                             VK_BUFFER_USAGE_TRANSFER_DST_BIT)); // color
    buffers.push_back(buffer(uint64_t(width) * height * 4,
                             VK_BUFFER_USAGE_TRANSFER_DST_BIT)); // depth
    color = image(VK_FORMAT_R8G8B8A8_UNORM,
                  VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                      VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
                  VK_IMAGE_ASPECT_COLOR_BIT);
    depth =
        image(VK_FORMAT_D32_SFLOAT,
              VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT |
                  VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
              VK_IMAGE_ASPECT_DEPTH_BIT);
    VkSamplerCreateInfo sc{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
    sc.magFilter = sc.minFilter = VK_FILTER_NEAREST;
    sc.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
    sc.addressModeU = sc.addressModeV = sc.addressModeW =
        VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
    VK(vkCreateSampler(device, &sc, nullptr, &sampler));
    std::array<VkDescriptorSetLayoutBinding, 8> bindings{};
    for (uint32_t i = 0; i < 8; i++) {
      bindings[i].binding = i;
      bindings[i].descriptorType =
          i == 6 ? VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER
                 : VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
      bindings[i].descriptorCount = 1;
      bindings[i].stageFlags =
          VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_VERTEX_BIT;
    }
    VkDescriptorSetLayoutCreateInfo sl{
        VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
    sl.bindingCount = 8;
    sl.pBindings = bindings.data();
    VK(vkCreateDescriptorSetLayout(device, &sl, nullptr, &setLayout));
    VkPushConstantRange range{VK_SHADER_STAGE_COMPUTE_BIT |
                                  VK_SHADER_STAGE_VERTEX_BIT,
                              0, sizeof(Push)};
    VkPipelineLayoutCreateInfo pl{
        VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
    pl.setLayoutCount = 1;
    pl.pSetLayouts = &setLayout;
    pl.pushConstantRangeCount = 1;
    pl.pPushConstantRanges = &range;
    VK(vkCreatePipelineLayout(device, &pl, nullptr, &layout));
    VkDescriptorPoolSize sizes[] = {
        {VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 14},
        {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 2}};
    VkDescriptorPoolCreateInfo dp{
        VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
    dp.maxSets = 2;
    dp.poolSizeCount = 2;
    dp.pPoolSizes = sizes;
    VK(vkCreateDescriptorPool(device, &dp, nullptr, &descriptors));
    VkDescriptorSetAllocateInfo da{
        VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
    da.descriptorPool = descriptors;
    da.descriptorSetCount = 1;
    da.pSetLayouts = &setLayout;
    VK(vkAllocateDescriptorSets(device, &da, &set));
    VK(vkAllocateDescriptorSets(device, &da, &swapSet));
    std::array<VkDescriptorBufferInfo, 8> bi{};
    std::array<VkWriteDescriptorSet, 8> writes{};
    VkDescriptorImageInfo ii{sampler, depth.view,
                             VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
    for (uint32_t i = 0; i < 8; i++) {
      writes[i] = {VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
      writes[i].dstSet = set;
      writes[i].dstBinding = i;
      writes[i].descriptorCount = 1;
      writes[i].descriptorType = bindings[i].descriptorType;
      if (i == 6)
        writes[i].pImageInfo = &ii;
      else {
        auto &b = buffers[i == 7 ? 6 : i];
        bi[i] = {b.buffer, 0, b.size};
        writes[i].pBufferInfo = &bi[i];
      }
    }
    vkUpdateDescriptorSets(device, 8, writes.data(), 0, nullptr);
    std::swap(bi[0], bi[1]);
    for (auto &w : writes)
      w.dstSet = swapSet;
    vkUpdateDescriptorSets(device, 8, writes.data(), 0, nullptr);
    clearPass = renderPass(false);
    loadPass = renderPass(true);
    VkImageView views[] = {color.view, depth.view};
    VkFramebufferCreateInfo fb{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};
    fb.renderPass = clearPass;
    fb.attachmentCount = 2;
    fb.pAttachments = views;
    fb.width = width;
    fb.height = height;
    fb.layers = 1;
    VK(vkCreateFramebuffer(device, &fb, nullptr, &framebuffer));
    VkQueryPoolCreateInfo qc{VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO};
    qc.queryType = VK_QUERY_TYPE_TIMESTAMP;
    qc.queryCount = 8;
    if (timestamps)
      VK(vkCreateQueryPool(device, &qc, nullptr, &queries));
    VkPipelineCacheCreateInfo cacheInfo{
        VK_STRUCTURE_TYPE_PIPELINE_CACHE_CREATE_INFO};
    VK(vkCreatePipelineCache(device, &cacheInfo, nullptr, &pipelineCache));
    auto pipelineStart = std::chrono::steady_clock::now();
    update = compute("update.comp");
    hiz = compute("hiz.comp");
    cull = compute("cull.comp");
    finalize = compute("finalize.comp");
    graphics = graphicsPipeline(0);
    additive = graphicsPipeline(1);
    alpha = graphicsPipeline(2);
    graphicsReverse = graphicsPipeline(0, true);
    additiveReverse = graphicsPipeline(1, true);
    alphaReverse = graphicsPipeline(2, true);
    size_t cacheBytes = 0;
    VK(vkGetPipelineCacheData(device, pipelineCache, &cacheBytes, nullptr));
    std::vector<uint8_t> cacheData(cacheBytes);
    VK(vkGetPipelineCacheData(device, pipelineCache, &cacheBytes,
                              cacheData.data()));
    cacheInfo.initialDataSize = cacheBytes;
    cacheInfo.pInitialData = cacheData.data();
    VkPipelineCache warmCache{};
    VK(vkCreatePipelineCache(device, &cacheInfo, nullptr, &warmCache));
    VK(vkMergePipelineCaches(device, pipelineCache, 1, &warmCache));
    vkDestroyPipelineCache(device, warmCache, nullptr);
    std::cout << "{\"pipeline_build_and_cache_roundtrip_ms\":"
              << std::chrono::duration<double, std::milli>(
                     std::chrono::steady_clock::now() - pipelineStart)
                     .count()
              << ",\"cache_bytes\":" << cacheBytes
              << ",\"speedup_claimed\":false}\n";
    std::cout << "{\"device\":\"" << properties.deviceName
              << "\",\"apiVersion\":" << properties.apiVersion
              << ",\"deviceType\":" << properties.deviceType
              << ",\"validation\":" << validation
              << ",\"firstInstance\":" << firstInstance
              << ",\"multiDrawIndirect\":" << mdi
              << ",\"drawIndirectCount\":" << countEnabled
              << ",\"allocated_bytes\":" << allocated << "}\n";
  }
  uint32_t memoryType(uint32_t bits, VkMemoryPropertyFlags flags) {
    for (uint32_t i = 0; i < mem.memoryTypeCount; i++)
      if ((bits & (1u << i)) &&
          (mem.memoryTypes[i].propertyFlags & flags) == flags)
        return i;
    throw std::runtime_error("Required memory property unavailable (fixture)");
  }
  Buffer buffer(VkDeviceSize size, VkBufferUsageFlags usage) {
    if (size > properties.limits.maxStorageBufferRange &&
        (usage & VK_BUFFER_USAGE_STORAGE_BUFFER_BIT))
      throw std::runtime_error("Storage range exceeded");
    Buffer b;
    b.size = size;
    VkBufferCreateInfo ci{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
    ci.size = size;
    ci.usage = usage;
    VK(vkCreateBuffer(device, &ci, nullptr, &b.buffer));
    VkMemoryRequirements req;
    vkGetBufferMemoryRequirements(device, b.buffer, &req);
    VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    ai.allocationSize = req.size;
    ai.memoryTypeIndex = memoryType(req.memoryTypeBits,
                                    VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                                        VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    VK(vkAllocateMemory(device, &ai, nullptr, &b.memory));
    VK(vkBindBufferMemory(device, b.buffer, b.memory, 0));
    VK(vkMapMemory(device, b.memory, 0, size, 0, &b.map));
    allocated += req.size;
    return b;
  }
  Image image(VkFormat format, VkImageUsageFlags usage,
              VkImageAspectFlags aspect) {
    VkImageFormatProperties props;
    VK(vkGetPhysicalDeviceImageFormatProperties(
        physical, format, VK_IMAGE_TYPE_2D, VK_IMAGE_TILING_OPTIMAL, usage, 0,
        &props));
    Image im;
    VkImageCreateInfo ci{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};
    ci.imageType = VK_IMAGE_TYPE_2D;
    ci.format = format;
    ci.extent = {width, height, 1};
    ci.mipLevels = ci.arrayLayers = 1;
    ci.samples = VK_SAMPLE_COUNT_1_BIT;
    ci.tiling = VK_IMAGE_TILING_OPTIMAL;
    ci.usage = usage;
    VK(vkCreateImage(device, &ci, nullptr, &im.image));
    VkMemoryRequirements req;
    vkGetImageMemoryRequirements(device, im.image, &req);
    VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
    ai.allocationSize = req.size;
    ai.memoryTypeIndex = memoryType(req.memoryTypeBits, 0);
    VK(vkAllocateMemory(device, &ai, nullptr, &im.memory));
    VK(vkBindImageMemory(device, im.image, im.memory, 0));
    VkImageViewCreateInfo vi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
    vi.image = im.image;
    vi.viewType = VK_IMAGE_VIEW_TYPE_2D;
    vi.format = format;
    vi.subresourceRange = {aspect, 0, 1, 0, 1};
    VK(vkCreateImageView(device, &vi, nullptr, &im.view));
    allocated += req.size;
    return im;
  }
  VkShaderModule shader(std::string name) {
    std::ifstream f(shaders + "/" + name + ".spv",
                    std::ios::binary | std::ios::ate);
    if (!f)
      throw std::runtime_error("Missing shader " + name);
    size_t bytes = f.tellg();
    if (bytes % 4)
      throw std::runtime_error("Bad SPIR-V length");
    std::vector<uint32_t> code(bytes / 4);
    f.seekg(0);
    f.read((char *)code.data(), bytes);
    VkShaderModuleCreateInfo ci{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
    ci.codeSize = bytes;
    ci.pCode = code.data();
    VkShaderModule result;
    VK(vkCreateShaderModule(device, &ci, nullptr, &result));
    return result;
  }
  VkPipeline compute(std::string name) {
    VkShaderModule sm = shader(name);
    VkComputePipelineCreateInfo ci{
        VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
    ci.stage = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};
    ci.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
    ci.stage.module = sm;
    ci.stage.pName = "main";
    ci.layout = layout;
    VkPipeline p;
    VkResult result =
        vkCreateComputePipelines(device, pipelineCache, 1, &ci, nullptr, &p);
    vkDestroyShaderModule(device, sm, nullptr);
    VK(result);
    pipelines.push_back(p);
    return p;
  }
  VkRenderPass renderPass(bool load) {
    VkAttachmentDescription at[2]{};
    at[0].format = VK_FORMAT_R8G8B8A8_UNORM;
    at[1].format = VK_FORMAT_D32_SFLOAT;
    for (int i = 0; i < 2; i++) {
      at[i].samples = VK_SAMPLE_COUNT_1_BIT;
      at[i].loadOp =
          load ? VK_ATTACHMENT_LOAD_OP_LOAD : VK_ATTACHMENT_LOAD_OP_CLEAR;
      at[i].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
      at[i].stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
      at[i].stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
      at[i].initialLayout =
          load ? (i ? VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
                    : VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
               : VK_IMAGE_LAYOUT_UNDEFINED;
      at[i].finalLayout = i ? VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
                            : VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    }
    VkAttachmentReference cr{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},
        dr{1, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL};
    VkSubpassDescription sub{};
    sub.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
    sub.colorAttachmentCount = 1;
    sub.pColorAttachments = &cr;
    sub.pDepthStencilAttachment = &dr;
    VkRenderPassCreateInfo ci{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO};
    ci.attachmentCount = 2;
    ci.pAttachments = at;
    ci.subpassCount = 1;
    ci.pSubpasses = &sub;
    VkRenderPass p;
    VK(vkCreateRenderPass(device, &ci, nullptr, &p));
    return p;
  }
  VkPipeline graphicsPipeline(int blend, bool reversed = false) {
    auto vs = shader("scene.vert"), fs = shader("scene.frag");
    VkPipelineShaderStageCreateInfo st[2]{};
    for (int i = 0; i < 2; i++) {
      st[i] = {VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO};
      st[i].stage =
          i ? VK_SHADER_STAGE_FRAGMENT_BIT : VK_SHADER_STAGE_VERTEX_BIT;
      st[i].module = i ? fs : vs;
      st[i].pName = "main";
    }
    VkPipelineVertexInputStateCreateInfo vi{
        VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
    VkPipelineInputAssemblyStateCreateInfo ia{
        VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
    ia.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
    VkViewport viewport{0, 0, float(width), float(height), 0, 1};
    VkRect2D rect{{0, 0}, {width, height}};
    VkPipelineViewportStateCreateInfo vp{
        VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
    vp.viewportCount = vp.scissorCount = 1;
    vp.pViewports = &viewport;
    vp.pScissors = &rect;
    VkPipelineRasterizationStateCreateInfo rs{
        VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
    rs.polygonMode = VK_POLYGON_MODE_FILL;
    rs.cullMode = VK_CULL_MODE_NONE;
    rs.lineWidth = 1;
    VkPipelineMultisampleStateCreateInfo ms{
        VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
    ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
    VkPipelineDepthStencilStateCreateInfo ds{
        VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO};
    ds.depthTestEnable = VK_TRUE;
    ds.depthWriteEnable = blend ? VK_FALSE : VK_TRUE;
    ds.depthCompareOp =
        reversed ? VK_COMPARE_OP_GREATER_OR_EQUAL : VK_COMPARE_OP_LESS_OR_EQUAL;
    // Reversed-Z uses dynamic compare via a separate pipeline below (not
    // enabled extension).
    VkPipelineColorBlendAttachmentState att{};
    att.colorWriteMask = 15;
    att.blendEnable = blend != 0;
    att.srcColorBlendFactor =
        blend == 2 ? VK_BLEND_FACTOR_SRC_ALPHA : VK_BLEND_FACTOR_ONE;
    att.dstColorBlendFactor =
        blend == 2 ? VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA : VK_BLEND_FACTOR_ONE;
    att.colorBlendOp = VK_BLEND_OP_ADD;
    att.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
    att.dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    att.alphaBlendOp = VK_BLEND_OP_ADD;
    VkPipelineColorBlendStateCreateInfo bs{
        VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
    bs.attachmentCount = 1;
    bs.pAttachments = &att;
    VkGraphicsPipelineCreateInfo ci{
        VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
    ci.stageCount = 2;
    ci.pStages = st;
    ci.pVertexInputState = &vi;
    ci.pInputAssemblyState = &ia;
    ci.pViewportState = &vp;
    ci.pRasterizationState = &rs;
    ci.pMultisampleState = &ms;
    ci.pDepthStencilState = &ds;
    ci.pColorBlendState = &bs;
    ci.layout = layout;
    ci.renderPass = clearPass;
    VkPipeline p;
    VkResult result =
        vkCreateGraphicsPipelines(device, pipelineCache, 1, &ci, nullptr, &p);
    vkDestroyShaderModule(device, vs, nullptr);
    vkDestroyShaderModule(device, fs, nullptr);
    VK(result);
    pipelines.push_back(p);
    return p;
  }
  void begin() {
    VK(vkResetCommandBuffer(cb, 0));
    VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
    bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    VK(vkBeginCommandBuffer(cb, &bi));
  }
  void submit() {
    VK(vkEndCommandBuffer(cb));
    VK(vkResetFences(device, 1, &fence));
    VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
    si.commandBufferCount = 1;
    si.pCommandBuffers = &cb;
    VK(vkQueueSubmit(queue, 1, &si, fence));
    VK(vkWaitForFences(device, 1, &fence, VK_TRUE, 30'000'000'000ull));
  }
  void push(Push p) {
    vkCmdPushConstants(cb, layout,
                       VK_SHADER_STAGE_COMPUTE_BIT | VK_SHADER_STAGE_VERTEX_BIT,
                       0, sizeof(p), &p);
  }
  void bindCompute(VkPipeline pipe, Push p, uint32_t groups) {
    vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_COMPUTE, pipe);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_COMPUTE, layout, 0, 1,
                            &set, 0, nullptr);
    push(p);
    vkCmdDispatch(cb, groups, 1, 1);
  }
  void barrier(VkPipelineStageFlags src, VkAccessFlags sa,
               VkPipelineStageFlags dst, VkAccessFlags da) {
    VkMemoryBarrier b{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
    b.srcAccessMask = sa;
    b.dstAccessMask = da;
    vkCmdPipelineBarrier(cb, src, dst, 0, 1, &b, 0, nullptr, 0, nullptr);
  }
  void transition(Image im, VkImageAspectFlags aspect, VkImageLayout old,
                  VkImageLayout next, VkPipelineStageFlags src,
                  VkAccessFlags sa, VkPipelineStageFlags dst,
                  VkAccessFlags da) {
    VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
    b.oldLayout = old;
    b.newLayout = next;
    b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    b.image = im.image;
    b.subresourceRange = {aspect, 0, 1, 0, 1};
    b.srcAccessMask = sa;
    b.dstAccessMask = da;
    vkCmdPipelineBarrier(cb, src, dst, 0, 0, nullptr, 0, nullptr, 1, &b);
  }
  void startPass(bool load, bool reversed = false) {
    VkClearValue values[2]{};
    values[0].color = {{0, 0, 0, 1}};
    values[1].depthStencil = {reversed ? 0.f : 1.f, 0};
    VkRenderPassBeginInfo rp{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};
    rp.renderPass = load ? loadPass : clearPass;
    rp.framebuffer = framebuffer;
    rp.renderArea = {{0, 0}, {width, height}};
    rp.clearValueCount = 2;
    rp.pClearValues = values;
    vkCmdBeginRenderPass(cb, &rp, VK_SUBPASS_CONTENTS_INLINE);
    vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_GRAPHICS, layout, 0, 1,
                            &set, 0, nullptr);
  }
  void copyImage(Image image, VkImageAspectFlags aspect, Buffer target) {
    VkBufferImageCopy copy{};
    copy.imageSubresource = {aspect, 0, 0, 1};
    copy.imageExtent = {width, height, 1};
    vkCmdCopyImageToBuffer(cb, image.image,
                           VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, target.buffer,
                           1, &copy);
  }
  void stamp(uint32_t index) {
    if (timestamps)
      vkCmdWriteTimestamp(cb, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, queries,
                          index);
  }
  ~Vulkan() {
    if (!device)
      return;
    vkDeviceWaitIdle(device);
    if (queries)
      vkDestroyQueryPool(device, queries, nullptr);
    for (auto p : pipelines)
      vkDestroyPipeline(device, p, nullptr);
    vkDestroyPipelineCache(device, pipelineCache, nullptr);
    vkDestroyFramebuffer(device, framebuffer, nullptr);
    vkDestroyRenderPass(device, clearPass, nullptr);
    vkDestroyRenderPass(device, loadPass, nullptr);
    vkDestroyDescriptorPool(device, descriptors, nullptr);
    vkDestroyPipelineLayout(device, layout, nullptr);
    vkDestroyDescriptorSetLayout(device, setLayout, nullptr);
    vkDestroySampler(device, sampler, nullptr);
    for (auto im : {color, depth}) {
      vkDestroyImageView(device, im.view, nullptr);
      vkDestroyImage(device, im.image, nullptr);
      vkFreeMemory(device, im.memory, nullptr);
    }
    for (auto b : buffers) {
      vkUnmapMemory(device, b.memory);
      vkDestroyBuffer(device, b.buffer, nullptr);
      vkFreeMemory(device, b.memory, nullptr);
    }
    vkDestroyFence(device, fence, nullptr);
    vkDestroyCommandPool(device, pool, nullptr);
    vkDestroyDevice(device, nullptr);
    if (messenger)
      ((PFN_vkDestroyDebugUtilsMessengerEXT)vkGetInstanceProcAddr(
          instance, "vkDestroyDebugUtilsMessengerEXT"))(instance, messenger,
                                                        nullptr);
    vkDestroyInstance(instance, nullptr);
  }
};
uint32_t mipWidth(uint32_t w, uint32_t l) {
  return std::max(1u, (w + (1u << l) - 1) >> l);
}
std::vector<float> pyramid(const float *depth, uint32_t width, uint32_t height,
                           bool reversed = false) {
  std::vector<float> result(depth, depth + width * height);
  uint32_t off = 0, w = width, h = height;
  while (w > 1 || h > 1) {
    uint32_t nw = (w + 1) / 2, nh = (h + 1) / 2;
    for (uint32_t y = 0; y < nh; y++)
      for (uint32_t x = 0; x < nw; x++) {
        float d = reversed ? 1.f : 0.f;
        for (uint32_t yy = 0; yy < 2; yy++)
          for (uint32_t xx = 0; xx < 2; xx++)
            if (2 * x + xx < w && 2 * y + yy < h)
              d = reversed
                      ? std::min(d, result[off + (2 * y + yy) * w + 2 * x + xx])
                      : std::max(d,
                                 result[off + (2 * y + yy) * w + 2 * x + xx]);
        result.push_back(d);
      }
    off += w * h;
    w = nw;
    h = nh;
  }
  return result;
}
struct Decision {
  bool visible;
  uint32_t lod;
};
Decision decide(Object o, Push p, const std::vector<float> &hi,
                bool noCull = false) {
  float x = (o.sphere[0] - p.viewX) * p.zoom, y = o.sphere[1] * p.zoom,
        z = o.sphere[2], r = o.sphere[3], sr = r * p.zoom;
  bool finite = std::isfinite(x) && std::isfinite(y) && std::isfinite(z) &&
                std::isfinite(r);
  bool visible = o.meta[3] != 0;
  if (finite && !noCull)
    visible = visible && !(x + sr < -1 || x - sr > 1 || y + sr < -1 ||
                           y - sr > 1 || z + r < 0 || z - r > 1);
  uint32_t lod = 0;
  if (p.flags & 1) {
    float pixels = sr * p.height;
    lod = pixels > 1.5f ? 0 : (pixels > 0.7f ? 1 : 2);
    if (std::abs(pixels - 1.5f) < 0.1f && o.meta[2] <= 1)
      lod = o.meta[2];
    if (std::abs(pixels - 0.7f) < 0.05f && o.meta[2] >= 1)
      lod = o.meta[2];
  }
  while (lod < 3 && !(o.meta[1] & (1u << lod)))
    lod++;
  visible = visible && lod < 3;
  if (visible && finite && (p.flags & 2) && z - r > 0 && !noCull) {
    float lx = (x - sr) * .5f + .5f, ly = (y - sr) * .5f + .5f,
          hx = (x + sr) * .5f + .5f, hy = (y + sr) * .5f + .5f;
    if (lx >= 0 && ly >= 0 && hx <= 1 && hy <= 1) {
      float span = std::max((hx - lx) * p.width, (hy - ly) * p.height);
      uint32_t level = std::min(
          p.level,
          uint32_t(std::max(0.f, std::floor(std::log2(std::max(1.f, span))))));
      uint32_t w = mipWidth(p.width, level), h = mipWidth(p.height, level),
               off = 0;
      for (uint32_t i = 0; i < level; i++)
        off += mipWidth(p.width, i) * mipWidth(p.height, i);
      int ax = std::clamp(int(std::floor(lx * p.width / (1u << level))), 0,
                          int(w - 1)),
          bx = std::clamp(int(std::floor(hx * p.width / (1u << level))), 0,
                          int(w - 1)),
          ay = std::clamp(int(std::floor(ly * p.height / (1u << level))), 0,
                          int(h - 1)),
          by = std::clamp(int(std::floor(hy * p.height / (1u << level))), 0,
                          int(h - 1));
      bool rev = p.flags & 8;
      float d = rev ? 1.f : 0.f;
      for (int yy = ay; yy <= by; yy++)
        for (int xx = ax; xx <= bx; xx++)
          d = rev ? std::min(d, hi[off + yy * w + xx])
                  : std::max(d, hi[off + yy * w + xx]);
      if (rev ? 1 - (z - r) < d - .0001f : z - r > d + .0001f)
        visible = false;
    }
  }
  return {visible, lod};
}
std::vector<Object> makeScene(uint32_t n, uint32_t seed) {
  std::vector<Object> scene(n);
  uint32_t state = seed;
  auto rnd = [&]() {
    state = state * 1664525u + 1013904223u;
    return float(state >> 8) / 16777216.f;
  };
  for (uint32_t i = 0; i < n; i++) {
    auto &o = scene[i];
    o.sphere[0] = (rnd() * 2 - 1) * 1.1f;
    o.sphere[1] = (rnd() * 2 - 1) * 1.1f;
    o.sphere[2] = .05f + .9f * (float(i) + .25f) / float(n);
    o.sphere[3] = .006f + float(i % 3) * .012f;
    o.meta[0] = i;
    o.meta[1] = i % 7 == 0 ? 4 : 7;
    o.meta[2] = i % 3;
    o.meta[3] = 1;
  }
  // Near plane, screen edge, wall hole and camera-plane intersections are
  // deliberate.
  if (n >= 4) {
    scene[0].sphere[2] = .002f;
    scene[1].sphere[0] = 1.f;
    scene[2].sphere[0] = -.001f;
    scene[3].sphere[1] = -1.f;
  }
  return scene;
}
struct Result {
  std::vector<uint8_t> image;
  std::vector<uint32_t> ids;
  uint32_t overflow = 0;
  double wallMs = 0;
};
Result run(Vulkan &v, const std::vector<Object> &scene, Push p,
           std::string mode, bool standardAlpha = false,
           uint32_t capacity = UINT32_MAX) {
  auto started = std::chrono::steady_clock::now();
  p.capacity = capacity == UINT32_MAX ? v.n : capacity;
  p.level = v.levels - 1;
  p.width = v.width;
  p.height = v.height;
  p.n = v.n;
  if (v.firstInstance)
    p.flags |= 16u;
  std::memcpy(v.buffers[0].map, scene.data(), scene.size() * sizeof(Object));
  // Current-frame trusted wall depth. No history is consumed after
  // camera/viewport changes.
  v.begin();
  if (v.timestamps)
    vkCmdResetQueryPool(v.cb, v.queries, 0, 8);
  v.stamp(0);
  v.barrier(VK_PIPELINE_STAGE_HOST_BIT, VK_ACCESS_HOST_WRITE_BIT,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_READ_BIT);
  v.bindCompute(v.update, p, (v.n + 63) / 64);
  if (p.flags & 4) {
    for (int step = 0; step < 2; step++) {
      v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                VK_ACCESS_SHADER_WRITE_BIT,
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
                VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT);
      std::swap(v.set, v.swapSet);
      v.bindCompute(v.update, p, (v.n + 63) / 64);
    }
  }
  v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_WRITE_BIT,
            VK_PIPELINE_STAGE_VERTEX_SHADER_BIT |
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT |
                VK_PIPELINE_STAGE_HOST_BIT,
            VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_HOST_READ_BIT);
  v.stamp(1);
  v.startPass(false, p.flags & 8);
  vkCmdBindPipeline(v.cb, VK_PIPELINE_BIND_POINT_GRAPHICS,
                    (p.flags & 8) ? v.graphicsReverse : v.graphics);
  Push wall = p;
  wall.mode = 3;
  v.push(wall);
  vkCmdDraw(v.cb, 6, 1, 0, 0);
  vkCmdEndRenderPass(v.cb);
  v.transition(v.depth, VK_IMAGE_ASPECT_DEPTH_BIT,
               VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
               VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
               VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT |
                   VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT,
               VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
               VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_READ_BIT);
  v.copyImage(v.depth, VK_IMAGE_ASPECT_DEPTH_BIT, v.buffers[8]);
  v.transition(v.depth, VK_IMAGE_ASPECT_DEPTH_BIT,
               VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
               VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
               VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_READ_BIT,
               VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_READ_BIT);
  v.barrier(VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_WRITE_BIT,
            VK_PIPELINE_STAGE_HOST_BIT, VK_ACCESS_HOST_READ_BIT);
  v.stamp(2);
  v.submit();
  auto cpuHi =
      pyramid((float *)v.buffers[8].map, v.width, v.height, p.flags & 8);
  auto *objects = (Object *)v.buffers[1].map;
  if (p.flags & 4) {
    float delta = float(int(p.tick % 7) - 3) * .004f;
    for (uint32_t i = 0; i < v.n; i++) {
      float expectedX = scene[i].sphere[0];
      for (int step = 0; step < 3; step++)
        expectedX += delta;
      if (std::abs(objects[i].sphere[0] - expectedX) > 1e-6f ||
          objects[i].meta[3] != (i % 5 == p.tick % 5 ? 0u : 1u))
        throw std::runtime_error("Particle ping-pong update mismatch");
    }
  }
  std::vector<Decision> expected(v.n);
  std::vector<uint32_t> expectedIds;
  for (uint32_t i = 0; i < v.n; i++) {
    expected[i] = decide(objects[i], p, cpuHi, mode == "none");
    if (expected[i].visible)
      expectedIds.push_back(i);
  }
  bool gpu = mode == "fixed" || mode == "count";
  bool compact = mode == "count" && v.countEnabled;
  if (mode == "count" && !compact)
    std::cout << "{\"fallback\":\"Count unavailable -> fixed slots\"}\n";
  std::memset(v.buffers[2].map, 0x7f, size_t(v.buffers[2].size));
  std::memset(v.buffers[4].map, 0xff, size_t(v.buffers[4].size));
  std::memset(v.buffers[6].map, 0, size_t(v.buffers[6].size));
  std::array<uint32_t, 3> lodCounts{};
  if (!gpu) {
    auto *ids = (uint32_t *)v.buffers[4].map;
    uint32_t k = 0;
    if (standardAlpha) {
      std::stable_sort(expectedIds.begin(), expectedIds.end(),
                       [&](uint32_t a, uint32_t b) {
                         return objects[a].sphere[2] > objects[b].sphere[2];
                       });
      for (auto id : expectedIds)
        ids[k++] = id;
    } else
      for (uint32_t l = 0; l < 3; l++)
        for (auto id : expectedIds)
          if (expected[id].lod == l) {
            ids[k++] = id;
            lodCounts[l]++;
          }
    for (uint32_t i = 0; i < v.n; i++)
      ((uint32_t *)v.buffers[6].map)[i] = expected[i].lod;
  }
  v.begin();
  v.stamp(3);
  v.barrier(VK_PIPELINE_STAGE_HOST_BIT, VK_ACCESS_HOST_WRITE_BIT,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT |
                VK_PIPELINE_STAGE_VERTEX_SHADER_BIT,
            VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT);
  if (gpu) {
    vkCmdFillBuffer(v.cb, v.buffers[3].buffer, 0, 16, 0);
    v.barrier(VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_WRITE_BIT,
              VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
              VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT);
    if (p.flags & 2) {
      for (uint32_t l = 0; l < v.levels; l++) {
        Push hp = p;
        hp.level = l;
        v.bindCompute(v.hiz, hp,
                      (mipWidth(v.width, l) * mipWidth(v.height, l) + 63) / 64);
        v.barrier(
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_WRITE_BIT,
            VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_READ_BIT);
      }
    }
    v.stamp(4);
    Push cp = p;
    cp.mode = compact ? 1 : 0;
    v.bindCompute(v.cull, cp, (v.n + 63) / 64);
    v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_WRITE_BIT,
              VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,
              VK_ACCESS_SHADER_READ_BIT | VK_ACCESS_SHADER_WRITE_BIT);
    if (compact)
      v.bindCompute(v.finalize, cp, 1);
    // All three resource roles: command/count -> indirect; objects/LOD/IDs ->
    // vertex; diagnostic -> host.
    v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_WRITE_BIT,
              VK_PIPELINE_STAGE_DRAW_INDIRECT_BIT |
                  VK_PIPELINE_STAGE_VERTEX_SHADER_BIT |
                  VK_PIPELINE_STAGE_HOST_BIT,
              VK_ACCESS_INDIRECT_COMMAND_READ_BIT | VK_ACCESS_SHADER_READ_BIT |
                  VK_ACCESS_HOST_READ_BIT);
  }
  if (!gpu)
    v.stamp(4);
  v.stamp(5);
  v.transition(v.depth, VK_IMAGE_ASPECT_DEPTH_BIT,
               VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
               VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
               VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_ACCESS_SHADER_READ_BIT,
               VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT |
                   VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,
               VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT |
                   VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT);
  v.barrier(VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
            VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            VK_ACCESS_COLOR_ATTACHMENT_READ_BIT |
                VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT);
  v.startPass(true, p.flags & 8);
  VkPipeline gp =
      (p.flags & 8)
          ? (standardAlpha
                 ? v.alphaReverse
                 : ((p.flags & 4) ? v.additiveReverse : v.graphicsReverse))
          : (standardAlpha ? v.alpha
                           : ((p.flags & 4) ? v.additive : v.graphics));
  vkCmdBindPipeline(v.cb, VK_PIPELINE_BIND_POINT_GRAPHICS, gp);
  Push draw = p;
  draw.mode = (gpu && !(compact && (p.flags & 4))) ? 0 : 1;
  draw.base = 0;
  v.push(draw);
  if (gpu) {
    if (compact && (p.flags & 4)) {
      vkCmdDrawIndirect(v.cb, v.buffers[2].buffer, uint64_t(v.n) * 16, 1, 16);
    } else if (compact) {
      if (p.capacity > v.properties.limits.maxDrawIndirectCount)
        throw std::runtime_error("Count capacity exceeds maxDrawIndirectCount");
      vkCmdDrawIndirectCount(v.cb, v.buffers[2].buffer, 0, v.buffers[3].buffer,
                             0, p.capacity, sizeof(VkDrawIndirectCommand));
    } else if (v.mdi && v.firstInstance) {
      for (uint32_t off = 0; off < v.n;) {
        uint32_t count =
            std::min(v.n - off, v.properties.limits.maxDrawIndirectCount);
        vkCmdDrawIndirect(v.cb, v.buffers[2].buffer, uint64_t(off) * 16, count,
                          16);
        off += count;
      }
    } else {
      for (uint32_t i = 0; i < v.n; i++) {
        draw.base = v.firstInstance ? 0 : i;
        v.push(draw);
        vkCmdDrawIndirect(v.cb, v.buffers[2].buffer, uint64_t(i) * 16, 1, 16);
      }
    }
  } else if (standardAlpha) {
    for (uint32_t i = 0; i < expectedIds.size(); i++)
      vkCmdDraw(v.cb, 3u << (2 - expected[expectedIds[i]].lod), 1, 0, i);
  } else {
    uint32_t first = 0;
    for (uint32_t l = 0; l < 3; l++) {
      if (lodCounts[l])
        vkCmdDraw(v.cb, 3u << (2 - l), lodCounts[l], 0, first);
      first += lodCounts[l];
    }
  }
  vkCmdEndRenderPass(v.cb);
  v.stamp(6);
  v.transition(v.color, VK_IMAGE_ASPECT_COLOR_BIT,
               VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
               VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
               VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
               VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
               VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_READ_BIT);
  v.copyImage(v.color, VK_IMAGE_ASPECT_COLOR_BIT, v.buffers[7]);
  v.barrier(VK_PIPELINE_STAGE_TRANSFER_BIT, VK_ACCESS_TRANSFER_WRITE_BIT,
            VK_PIPELINE_STAGE_HOST_BIT, VK_ACCESS_HOST_READ_BIT);
  v.stamp(7);
  v.submit();
  if (v.timestamps) {
    uint64_t ts[8]{};
    VK(vkGetQueryPoolResults(v.device, v.queries, 0, 8, sizeof(ts), ts, 8,
                             VK_QUERY_RESULT_64_BIT |
                                 VK_QUERY_RESULT_WAIT_BIT));
    double scale = v.properties.limits.timestampPeriod / 1e6;
    uint64_t mask = v.timestampBits == 64
                        ? UINT64_MAX
                        : ((uint64_t(1) << v.timestampBits) - 1);
    auto elapsed = [&](int start, int end) {
      return ((ts[end] - ts[start]) & mask) * scale;
    };
    std::cout << "{\"gpu_timestamps_ms\":{\"update\":" << elapsed(0, 1)
              << ",\"wall_depth_readback\":" << elapsed(1, 2)
              << ",\"hiz\":" << elapsed(3, 4)
              << ",\"cull_finalize\":" << elapsed(4, 5)
              << ",\"draw\":" << elapsed(5, 6)
              << ",\"readback\":" << elapsed(6, 7) << "}}\n";
  }
  Result result;
  result.image.assign((uint8_t *)v.buffers[7].map,
                      (uint8_t *)v.buffers[7].map + v.width * v.height * 4);
  if (gpu) {
    auto *cmds = (VkDrawIndirectCommand *)v.buffers[2].map;
    auto *ids = (uint32_t *)v.buffers[4].map;
    auto *counts = (uint32_t *)v.buffers[3].map;
    result.overflow = compact ? counts[1] : 0;
    uint32_t count = compact ? counts[0] : v.n;
    if (count > p.capacity && compact)
      throw std::runtime_error("Unclamped count");
    for (uint32_t i = 0; i < count; i++)
      if (cmds[i].instanceCount) {
        uint32_t id = compact ? ids[i] : i;
        if (id >= v.n || !expected[id].visible ||
            cmds[i].vertexCount != (3u << (2 - expected[id].lod)) ||
            cmds[i].firstVertex != 0 ||
            cmds[i].firstInstance != (v.firstInstance ? id : 0))
          throw std::runtime_error("GPU command/visibility/residency mismatch");
        result.ids.push_back(id);
      }
    auto sorted = expectedIds;
    std::sort(sorted.begin(), sorted.end());
    std::sort(result.ids.begin(), result.ids.end());
    if (!result.overflow && result.ids != sorted)
      throw std::runtime_error("CPU/GPU visible IDs differ");
    if (std::adjacent_find(result.ids.begin(), result.ids.end()) !=
        result.ids.end())
      throw std::runtime_error("Duplicate compact IDs");
    if (((uint32_t *)v.buffers[2].map)[(v.n + 1) * 4] != 0x7f7f7f7f ||
        ids[v.n] != 0xffffffffu)
      throw std::runtime_error("OOB guard changed");
    if (p.flags & 2) {
      auto *actual = (float *)v.buffers[5].map;
      for (size_t i = 0; i < cpuHi.size(); i++)
        if (std::abs(actual[i] - cpuHi[i]) > 1e-6f)
          throw std::runtime_error("HiZ pyramid mismatch");
    }
  } else
    result.ids = expectedIds;
  if (!artifactDirectory.empty()) {
    std::string stem = artifactDirectory + "/" +
                       std::to_string(artifactSequence++) + "-" + mode;
    std::ofstream imageFile(stem + ".rgba", std::ios::binary);
    imageFile.write(reinterpret_cast<const char *>(result.image.data()),
                    result.image.size());
    std::ofstream idsFile(stem + ".ids", std::ios::binary);
    idsFile.write(reinterpret_cast<const char *>(result.ids.data()),
                  result.ids.size() * sizeof(uint32_t));
    std::ofstream meta(stem + ".json");
    meta << "{\"width\":" << v.width << ",\"height\":" << v.height
         << ",\"format\":\"RGBA8_UNORM\",\"id_format\":\"uint32-native-"
            "endian\",\"mode\":\""
         << mode << "\",\"flags\":" << p.flags << ",\"viewX\":" << p.viewX
         << ",\"zoom\":" << p.zoom << ",\"capacity\":" << p.capacity << "}";
  }
  result.wallMs = std::chrono::duration<double, std::milli>(
                      std::chrono::steady_clock::now() - started)
                      .count();
  std::cout << "{\"mode\":\"" << mode << "\",\"flags\":" << p.flags
            << ",\"viewX\":" << p.viewX << ",\"instances\":" << v.n
            << ",\"visible\":" << result.ids.size()
            << ",\"overflow\":" << result.overflow
            << ",\"host_wall_ms_with_readbacks\":" << result.wallMs << "}\n";
  return result;
}
void compare(const Result &a, const Result &b, uint32_t tolerance = 0) {
  if (a.image.size() != b.image.size())
    throw std::runtime_error("image size");
  uint32_t errors = 0;
  for (size_t i = 0; i < a.image.size(); i++)
    if (std::abs(int(a.image[i]) - int(b.image[i])) > int(tolerance))
      errors++;
  if (errors)
    throw std::runtime_error("Image mismatch channels=" +
                             std::to_string(errors));
}
int main(int argc, char **argv) {
  try {
    uint32_t n = 1000;
    bool low = false;
    std::string shaders = "build/shaders";
    for (int i = 1; i < argc; i++) {
      std::string arg = argv[i];
      if (arg == "--instances" && i + 1 < argc)
        n = std::stoul(argv[++i]);
      else if (arg == "--shaders" && i + 1 < argc)
        shaders = argv[++i];
      else if (arg == "--artifacts" && i + 1 < argc) {
        artifactDirectory = argv[++i];
        if (std::filesystem::exists(artifactDirectory))
          throw std::runtime_error("Refuse existing artifact directory");
        std::filesystem::create_directories(artifactDirectory);
      } else if (arg == "--force-low")
        low = true;
      else
        throw std::runtime_error(
            "usage: --instances 1000|10000|100000 --shaders DIR --force-low");
    }
    if (n != 1000 && n != 10000 && n != 100000)
      throw std::runtime_error("Unsupported workload (no silent downscale)");
    Vulkan vk(n, shaders, low);
    auto scene = makeScene(n, 0x5eed);
    Push p{};
    p.zoom = 1;
    p.tick = 1;
    for (float view : {0.f, .75f, 1.8f, 2.5f}) {
      p.viewX = view;
      p.zoom = view == 0.f ? .8f : 1.f;
      for (uint32_t flags : {0u, 1u, 2u, 3u, 4u, 8u, 10u, 11u}) {
        p.flags = flags;
        auto cpu = run(vk, scene, p, "cpu");
        auto fixed = run(vk, scene, p, "fixed");
        compare(cpu, fixed);
        auto compact = run(vk, scene, p, "count");
        compare(cpu, compact, flags & 4 ? 1 : 0);
        if (flags == 0 || (flags & 2)) {
          auto none = run(vk, scene, p, "none");
          compare(cpu, none);
        }
      }
    }
    p.viewX = 0;
    p.flags = 4;
    auto alphaA = run(vk, scene, p, "cpu", true);
    auto alphaB = run(vk, scene, p, "cpu", true);
    compare(alphaA, alphaB);
    if (vk.countEnabled) {
      p.flags = 0;
      auto zeroCapacity = run(vk, scene, p, "count", false, 0);
      if (!zeroCapacity.overflow || !zeroCapacity.ids.empty())
        throw std::runtime_error("Zero capacity must remain bounded");
      auto overflow = run(vk, scene, p, "count", false, 8);
      if (!overflow.overflow)
        throw std::runtime_error("Expected bounded overflow");
      auto fallback = run(vk, scene, p, "fixed");
      auto cpu = run(vk, scene, p, "cpu");
      compare(fallback, cpu);
    }
    if (validationErrors)
      throw std::runtime_error("Validation errors=" +
                               std::to_string(validationErrors));
    std::cout << "{\"status\":\"PASS\",\"seed\":24301,\"instances\":" << n
              << ",\"validation_errors\":0,\"scope\":\"offscreen Vulkan "
                 "correctness, not mobile performance\"}\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << "FAIL: " << e.what() << "\n";
    return 1;
  }
}
