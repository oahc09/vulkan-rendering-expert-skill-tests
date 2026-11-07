// SPDX-License-Identifier: MIT
// Adapted locally from Engine Scale Lab; no shared fixture changes.
  VkPipeline labPipeline(int blend) {
    auto vs = shader("lab.vert"), fs = shader("lab.frag");
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
        VK_COMPARE_OP_LESS_OR_EQUAL;
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
    att.dstAlphaBlendFactor = blend == 1 ? VK_BLEND_FACTOR_ONE : VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    if(blend==3){att.srcColorBlendFactor=VK_BLEND_FACTOR_ZERO;att.dstColorBlendFactor=VK_BLEND_FACTOR_ONE_MINUS_SRC_COLOR;att.srcAlphaBlendFactor=VK_BLEND_FACTOR_ZERO;att.dstAlphaBlendFactor=VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;}
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
  VkRenderPass labPass(VkFormat format) {
    VkAttachmentDescription at[2]{};
    at[0].format = format;
    at[1].format = VK_FORMAT_D32_SFLOAT;
    for (int i = 0; i < 2; i++) {
      at[i].samples = VK_SAMPLE_COUNT_1_BIT;
      at[i].loadOp =
          VK_ATTACHMENT_LOAD_OP_CLEAR;
      at[i].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
      at[i].stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
      at[i].stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
      at[i].initialLayout =
          VK_IMAGE_LAYOUT_UNDEFINED;
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
