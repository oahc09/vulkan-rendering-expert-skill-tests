// SPDX-License-Identifier: MIT
// Reuses official Vulkan setup only; old two-generation experiment unchanged.
#define main old_inflight_main
#include "../text_inflight_lab/main.cpp"
#undef main
struct Churn:Lab {
 std::array<VkFence,3> fences{};std::array<VkCommandBuffer,3> work{};uint64_t releaseGate=0;
 Churn(){
  for(auto& f:fences){VkFenceCreateInfo ci{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};VK(vkCreateFence(device,&ci,nullptr,&f));}
  // Persistent recording, no ONE_TIME_SUBMIT. UNDEFINED discards the old image
  // only after the prior generation's two consumers and fences are complete.
  for(int j=0;j<3;j++){
   VkCommandBufferAllocateInfo ai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};ai.commandPool=pool;ai.level=VK_COMMAND_BUFFER_LEVEL_PRIMARY;ai.commandBufferCount=1;VK(vkAllocateCommandBuffers(device,&ai,&work[j]));commands.push_back(work[j]);
   VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};VK(vkBeginCommandBuffer(work[j],&bi));auto cb=work[j];
   VkBufferImageCopy cp{};cp.imageSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};cp.imageExtent={W,H,1};
   VkMemoryBarrier mb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
   if(j==0){mb.srcAccessMask=VK_ACCESS_HOST_WRITE_BIT;mb.dstAccessMask=VK_ACCESS_TRANSFER_READ_BIT;vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_HOST_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,0,1,&mb,0,nullptr,0,nullptr);
    imageBarrier(cb,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,0,VK_ACCESS_TRANSFER_WRITE_BIT);vkCmdCopyBufferToImage(cb,buffers[0].handle,slot,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&cp);imageBarrier(cb,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_TRANSFER_READ_BIT);
   }else{vkCmdCopyImageToBuffer(cb,slot,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,buffers[j+1].handle,1,&cp);mb.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;mb.dstAccessMask=VK_ACCESS_HOST_READ_BIT;vkCmdPipelineBarrier(cb,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_HOST_BIT,0,1,&mb,0,nullptr,0,nullptr);}
   VK(vkEndCommandBuffer(cb));
  }
 }
 void launch(int j,std::vector<VkSemaphore> waits,std::vector<uint64_t> values,VkSemaphore signal,uint64_t value){
  VK(vkResetFences(device,1,&fences[j]));std::vector<VkPipelineStageFlags> stages(waits.size(),VK_PIPELINE_STAGE_TRANSFER_BIT);
  VkTimelineSemaphoreSubmitInfo ts{VK_STRUCTURE_TYPE_TIMELINE_SEMAPHORE_SUBMIT_INFO};ts.waitSemaphoreValueCount=values.size();ts.pWaitSemaphoreValues=values.data();ts.signalSemaphoreValueCount=1;ts.pSignalSemaphoreValues=&value;
  VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};si.pNext=&ts;si.waitSemaphoreCount=waits.size();si.pWaitSemaphores=waits.data();si.pWaitDstStageMask=stages.data();si.commandBufferCount=1;si.pCommandBuffers=&work[j];si.signalSemaphoreCount=1;si.pSignalSemaphores=&signal;
  VK(vkQueueSubmit(queue,1,&si,fences[j]));submissionFences.push_back(fences[j]);
 }
 void completeRound(){VK(vkWaitForFences(device,submissionFences.size(),submissionFences.data(),VK_TRUE,10'000'000'000ull));submissionFences.clear();}
 ~Churn(){
  // Unblock all submitted work even if an exception occurred mid-generation.
  uint64_t current=0;vkGetSemaphoreCounterValue(device,gate,&current);if(current<releaseGate){VkSemaphoreSignalInfo s{VK_STRUCTURE_TYPE_SEMAPHORE_SIGNAL_INFO};s.semaphore=gate;s.value=releaseGate;vkSignalSemaphore(device,&s);}
  if(!submissionFences.empty()){auto r=vkWaitForFences(device,submissionFences.size(),submissionFences.data(),VK_TRUE,10'000'000'000ull);if(r!=VK_SUCCESS){std::cerr<<"CHURN_CLEANUP_TIMEOUT"<<std::endl;std::_Exit(2);}}
  submissionFences.clear();for(auto f:fences)if(f)vkDestroyFence(device,f,nullptr);
 }
};
int main(int argc,char**argv){try{
 if(argc!=2 && !(argc==3 && std::string(argv[2])=="--abort-pending"))throw std::runtime_error("usage: churn_lab NEW_OUTPUT [--abort-pending]");
 std::filesystem::path out=argv[1];if(!std::filesystem::create_directory(out))throw std::runtime_error("refuse existing output");
 {Churn v;std::ofstream log(out/"generations.jsonl");
 for(int gen=0;gen<64;gen++){
  uint64_t base=2*gen,last=base+2;v.releaseGate=last;
  if(!v.reusable(base))throw std::runtime_error("prior consumers still pending");
  auto* p=static_cast<float*>(v.buffers[0].mapped);for(unsigned i=0;i<Lab::N;i++)p[i]=float(gen+1)*.25f+float(i%17)/1024;
  v.launch(0,{v.gate},{base+1},v.ready,gen+1);v.launch(1,{v.ready},{uint64_t(gen+1)},v.done,base+1);v.launch(2,{v.gate,v.done},{last,base+1},v.done,last);
  if(argc==3 && gen==31)throw std::runtime_error("INTENTIONAL_ABORT_PENDING_GENERATION_31");
  auto pending=v.completed();if(pending!=base||v.reusable(last))throw std::runtime_error("early reuse before A");
  v.hostGate(base+1);v.waitDone(base+1);auto partial=v.completed();if(partial!=base+1||v.reusable(last))throw std::runtime_error("early reuse before B");
  v.hostGate(last);v.waitDone(last);if(!v.reusable(last))throw std::runtime_error("completed slot not reusable");v.completeRound();
  for(int consumer=0;consumer<2;consumer++){auto* read=static_cast<float*>(v.buffers[consumer+2].mapped);for(unsigned i=0;i<Lab::N;i++)if(!std::isfinite(read[i])||read[i]!=p[i])throw std::runtime_error("generation bytes mismatch");std::ofstream raw(out/("g"+std::to_string(gen)+"-c"+std::to_string(consumer)+".f32"),std::ios::binary);raw.write(reinterpret_cast<char*>(read),Lab::N*4);}
  if(v.buffers.size()!=5||v.commands.size()!=3||!v.submissionFences.empty())throw std::runtime_error("fixture resource growth");
  log<<"{\"generation\":"<<gen<<",\"pending\":"<<pending<<",\"partial\":"<<partial<<",\"complete\":"<<v.completed()<<",\"reuse_before_A\":false,\"reuse_before_B\":false,\"reuse_after_B\":true,\"image_slots\":1,\"buffers\":5,\"commands\":3,\"fences\":3,\"semaphores\":3,\"pending_fences_after_wait\":0}\n";
 }
 std::ofstream summary(out/"numerics.json");summary<<"{\"generations\":64,\"readbacks\":128,\"final_counter\":"<<v.completed()<<",\"validation_enabled\":"<<(v.validation?"true":"false")<<",\"max_error\":0}\n";
 }
 if(diagnostics)throw std::runtime_error("validation diagnostics");std::cout<<"CHURN_RESOURCES_DESTROYED\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
