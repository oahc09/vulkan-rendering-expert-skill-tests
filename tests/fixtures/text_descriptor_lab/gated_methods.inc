 VkSemaphore drawGate{};bool injectFailure=false;int descriptorIdentity=0;
 void gatedBegin(){VkSemaphoreTypeCreateInfo ti{VK_STRUCTURE_TYPE_SEMAPHORE_TYPE_CREATE_INFO};ti.semaphoreType=VK_SEMAPHORE_TYPE_TIMELINE;VkSemaphoreCreateInfo ci{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};ci.pNext=&ti;VK(vkCreateSemaphore(device,&ci,nullptr,&drawGate));begin();}

 void gatedSubmit(){
  VK(vkEndCommandBuffer(cb));VK(vkResetFences(device,1,&fence));VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};si.commandBufferCount=1;si.pCommandBuffers=&cb;uint64_t gateValue=1;VkTimelineSemaphoreSubmitInfo timeline{VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO};timeline.waitSemaphoreValueCount=1;timeline.pWaitSemaphoreValues=&gateValue;VkPipelineStageFlags stage=VK_PIPELINE_STAGE_ALL_COMMANDS_BIT;si.pNext=&timeline;si.waitSemaphoreCount=1;si.pWaitSemaphores=&drawGate;si.pWaitDstStageMask=&stage;VK(vkQueueSubmit(queue,1,&si,fence));
  // Once submitted, ALWAYS release the host timeline and await completion before
  // allowing destruction; no unbounded inherited device-idle on failure.
  auto pending=vkGetFenceStatus(device,fence);
  VkSemaphoreSignalInfo signal{VK_STRUCTURE_TYPE_SEMAPHORE_SIGNAL_INFO};signal.semaphore=drawGate;signal.value=1;VkResult signaled=vkSignalSemaphore(device,&signal);
  if(signaled!=VK_SUCCESS){std::cerr<<"DRAW_GATE_SIGNAL_FAILURE"<<std::endl;std::_Exit(2);}
  auto waited=vkWaitForFences(device,1,&fence,VK_TRUE,10'000'000'000ull);
  if(waited!=VK_SUCCESS){std::cerr<<"DRAW_GATE_CLEANUP_TIMEOUT"<<std::endl;std::_Exit(2);}
  vkDestroySemaphore(device,drawGate,nullptr);drawGate=VK_NULL_HANDLE;
  if(pending!=VK_NOT_READY)throw std::runtime_error("draw was not genuinely pending");
  std::cout<<"{\"descriptor\":"<<descriptorIdentity<<",\"pending_fence_not_ready\":true,\"retired_fence_success\":true}\n";
  if(injectFailure)throw std::runtime_error("INTENTIONAL_PENDING_DRAW_CLEANED");
 }
