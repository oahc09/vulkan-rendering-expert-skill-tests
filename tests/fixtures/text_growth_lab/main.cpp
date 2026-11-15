// SPDX-License-Identifier: MIT
#define main inherited_lab_main
#include "../text_inflight_lab/main.cpp"
#undef main
struct Growth:Lab {
 VkImage candidate{};VkDeviceMemory candidateMemory{};uint64_t release=0;unsigned created=1,destroyed=0;
 void createPage(){if(candidate)throw std::runtime_error("candidate already exists");VkImageCreateInfo ic{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};ic.imageType=VK_IMAGE_TYPE_2D;ic.format=VK_FORMAT_R32_SFLOAT;ic.extent={W,H,1};ic.mipLevels=ic.arrayLayers=1;ic.samples=VK_SAMPLE_COUNT_1_BIT;ic.tiling=VK_IMAGE_TILING_OPTIMAL;ic.usage=VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_TRANSFER_SRC_BIT;VK(vkCreateImage(device,&ic,nullptr,&candidate));VkMemoryRequirements req;vkGetImageMemoryRequirements(device,candidate,&req);VkMemoryAllocateInfo a{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};a.allocationSize=req.size;a.memoryTypeIndex=memoryType(req.memoryTypeBits,0);VK(vkAllocateMemory(device,&a,nullptr,&candidateMemory));VK(vkBindImageMemory(device,candidate,candidateMemory,0));created++;}
 void reclaim(){if(!submissionFences.empty()){VK(vkWaitForFences(device,submissionFences.size(),submissionFences.data(),VK_TRUE,10'000'000'000ull));for(auto f:submissionFences)vkDestroyFence(device,f,nullptr);submissionFences.clear();}if(candidate){vkDestroyImage(device,candidate,nullptr);vkFreeMemory(device,candidateMemory,nullptr);candidate=VK_NULL_HANDLE;candidateMemory=VK_NULL_HANDLE;destroyed++;}}
 struct ScopedSlot {Growth& v;VkImage old;ScopedSlot(Growth& x):v(x),old(x.slot){v.slot=v.candidate;}~ScopedSlot(){v.slot=old;}};
 VkCommandBuffer uploadCandidate(bool inject=false){ScopedSlot swap(*this);if(inject)throw std::runtime_error("INTENTIONAL_RECORD_FAILURE_RESTORED");return producer(0);}
 VkCommandBuffer readPublished(int generation){if(generation==0)return consumer(2);if(generation==2)return readCandidate();throw std::runtime_error("unpublished generation routed");}
 VkCommandBuffer readCandidate(){ScopedSlot swap(*this);return consumer(2);}
 ~Growth(){uint64_t v=0;vkGetSemaphoreCounterValue(device,gate,&v);if(v<release){VkSemaphoreSignalInfo s{VK_STRUCTURE_TYPE_SEMAPHORE_SIGNAL_INFO};s.semaphore=gate;s.value=release;vkSignalSemaphore(device,&s);}try{reclaim();}catch(...){std::cerr<<"GROWTH_CLEANUP_TIMEOUT"<<std::endl;std::_Exit(2);}}
};
static void pattern(Buffer& b,int gen){auto p=static_cast<float*>(b.mapped);for(unsigned i=0;i<Lab::N;i++)p[i]=(gen+1)*.25f+(i%17)/1024.f;}
static void dump(Growth& v,int index,int gen,const std::filesystem::path& path){auto p=static_cast<float*>(v.buffers[index].mapped);for(unsigned i=0;i<Lab::N;i++)if(p[i]!=(gen+1)*.25f+(i%17)/1024.f)throw std::runtime_error("wrong generation");std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<char*>(p),Lab::N*4);if(!f)throw std::runtime_error("write failed");}
int main(int argc,char**argv){try{
 if(argc!=2 && !(argc==3 && (std::string(argv[2])=="--abort-pending"||std::string(argv[2])=="--abort-recording")))throw std::runtime_error("usage growth NEW_OUTPUT [--abort-pending]");
 std::filesystem::path out=argv[1];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");
 {Growth v;std::ofstream events(out/"events.jsonl");int published=0;
 pattern(v.buffers[0],0);auto oldUpload=v.producer(0);v.submit(oldUpload,{}, {},v.done,1);v.waitDone(1);
 // Ensure upload fence finished before reusing staging for canceled generation.
 VK(vkWaitForFences(v.device,v.submissionFences.size(),v.submissionFences.data(),VK_TRUE,10'000'000'000ull));
 v.createPage();if(argc==3 && std::string(argv[2])=="--abort-recording"){auto original=v.slot;try{v.uploadCandidate(true);}catch(...){if(v.slot!=original){std::cerr<<"SLOT_NOT_RESTORED"<<std::endl;std::_Exit(2);}throw;}}pattern(v.buffers[0],1);auto a=v.consumer(0),b=v.consumer(1),cu=v.uploadCandidate(),cr=v.readCandidate();v.release=2;
 v.submit(a,{v.gate},{1},v.done,2);v.submit(b,{v.gate,v.done},{2,2},v.done,3);v.submit(cu,{v.done},{3},v.ready,1);v.submit(cr,{v.ready},{1},v.done,4);
 // Cancellation changes host routing, never cancels queued GPU operations.
 events<<"{\"phase\":\"cancel_pending\",\"published\":0,\"live_pages\":2,\"completed\":"<<v.completed()<<"}\n";
 if(argc==3)throw std::runtime_error("INTENTIONAL_GROWTH_CANCEL_PENDING");
 if(v.completed()!=1||published!=0)throw std::runtime_error("cancel route changed");
 v.hostGate(1);v.waitDone(2);if(v.completed()!=2)throw std::runtime_error("B not blocked");events<<"{\"phase\":\"A_done_B_pending\",\"published\":0,\"live_pages\":2,\"completed\":2}\n";
 v.hostGate(2);v.waitDone(4);dump(v,2,0,out/"old-A.f32");dump(v,3,0,out/"old-B.f32");dump(v,4,1,out/"cancel-diagnostic.f32");
 // Published route must still target old page after canceled upload completion.
 auto route=v.readPublished(published);v.submit(route,{v.done},{4},v.done,5);v.waitDone(5);dump(v,4,0,out/"route-after-cancel.f32");v.reclaim();events<<"{\"phase\":\"canceled_reclaimed\",\"published\":0,\"live_pages\":1,\"completed\":5}\n";
 v.createPage();pattern(v.buffers[0],2);auto newUpload=v.uploadCandidate();v.submit(newUpload,{}, {},v.ready,2);
 uint64_t ready=2;VkSemaphoreWaitInfo wi{VK_STRUCTURE_TYPE_SEMAPHORE_WAIT_INFO};wi.semaphoreCount=1;wi.pSemaphores=&v.ready;wi.pValues=&ready;VK(vkWaitSemaphores(v.device,&wi,10'000'000'000ull));
 published=2;auto newRoute=v.readPublished(published);v.submit(newRoute,{v.ready},{2},v.done,6);v.waitDone(6);dump(v,4,published,out/"published-new.f32");
 // Both old consumers and every submission are retired before old page release.
 VK(vkWaitForFences(v.device,v.submissionFences.size(),v.submissionFences.data(),VK_TRUE,10'000'000'000ull));
 vkDestroyImage(v.device,v.slot,nullptr);vkFreeMemory(v.device,v.imageMemory,nullptr);v.destroyed++;v.slot=v.candidate;v.imageMemory=v.candidateMemory;v.candidate=VK_NULL_HANDLE;v.candidateMemory=VK_NULL_HANDLE;
 events<<"{\"phase\":\"new_published_old_retired\",\"published\":2,\"live_pages\":1,\"completed\":6}\n";
 std::ofstream n(out/"numerics.json");n<<"{\"validation_enabled\":"<<(v.validation?"true":"false")<<",\"page_creates\":"<<v.created<<",\"pages_destroyed_before_final_cleanup\":"<<v.destroyed<<",\"peak_live_pages\":2,\"final_route_generation\":"<<published<<",\"readbacks\":5,\"max_error\":0}\n";
 }
 if(diagnostics)throw std::runtime_error("validation diagnostics");std::cout<<"GROWTH_RESOURCES_DESTROYED\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
