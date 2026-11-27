// SPDX-License-Identifier: MIT
#include "budget_helper.hpp"
#include <limits>
struct Budget {
 Engine& e;uint64_t epoch=0,epochBytes=0,inflightBytes=0;unsigned inflight=0,accepted=0;PageResources* candidate=nullptr;SubmissionResources* upload=nullptr;
 static constexpr uint64_t capacity=65*49*4;
 explicit Budget(Engine& e):e(e){}
 void nextEpoch(uint64_t n){if(n<=epoch)throw std::runtime_error("epoch_not_increasing");epoch=n;epochBytes=0;}
 PageResources& request(double width,double height,const std::vector<float>& mask,int generation){
  if(!std::isfinite(width)||!std::isfinite(height))throw std::runtime_error("dimension_nonfinite");
  if(width<=0||height<=0||std::floor(width)!=width||std::floor(height)!=height||width>UINT32_MAX||height>UINT32_MAX)throw std::runtime_error("dimension_invalid");
  uint64_t w=uint64_t(width),h=uint64_t(height);
  if(w>std::numeric_limits<uint64_t>::max()/h/4)throw std::runtime_error("payload_overflow");uint64_t bytes=w*h*4;
  if(w!=65||h!=49)throw std::runtime_error("extent_unsupported");
  if(mask.size()!=w*h)throw std::runtime_error("mask_size");
  for(float x:mask)if(!std::isfinite(x)||x<0||x>1)throw std::runtime_error("mask_nonfinite_or_range");
  if(bytes>capacity-epochBytes)throw std::runtime_error("epoch_byte_limit");
  if(inflight>=1||bytes>capacity-inflightBytes)throw std::runtime_error("inflight_upload_limit");
  // Every deliberate input/budget rejection above precedes any Engine side effect.
  auto& p=e.page(generation);auto& s=e.upload(p,mask);candidate=&p;upload=&s;epochBytes+=bytes;inflightBytes+=bytes;++inflight;++accepted;return p;
 }
 void releaseSubmission(SubmissionResources& s){if(s.pending)throw std::runtime_error("release_pending_submission");for(auto& p:e.pages)if(p->uploadSubmission==&s)p->uploadSubmission=nullptr;
  if(s.fb)vkDestroyFramebuffer(e.v.device,s.fb,nullptr);e.freeImage(s.target);e.freeImage(s.velocity);e.freeImage(s.id);e.freeBuffer(s.staging);e.freeBuffer(s.vertices);e.freeBuffer(s.colorRead);e.freeBuffer(s.velocityRead);e.freeBuffer(s.idRead);vkDestroyFence(e.v.device,s.fence,nullptr);vkFreeCommandBuffers(e.v.device,e.v.pool,1,&s.cb);
  auto* released=&s;e.submissions.erase(std::remove_if(e.submissions.begin(),e.submissions.end(),[&](auto& p){return p.get()==released;}),e.submissions.end());
 }
 void complete(){if(!upload||!candidate||!inflight)throw std::runtime_error("no_upload");if(vkGetFenceStatus(e.v.device,upload->fence)!=VK_SUCCESS)throw std::runtime_error("upload_not_complete");e.wait(*upload);auto* s=upload;upload=nullptr;candidate=nullptr;--inflight;inflightBytes-=capacity;releaseSubmission(*s);}
 void retire(PageResources& p){e.retire(p);auto* retired=&p;e.pages.erase(std::remove_if(e.pages.begin(),e.pages.end(),[&](auto& x){return x.get()==retired;}),e.pages.end());}
 uint64_t residentStagingPayload(){uint64_t n=0;for(auto& s:e.submissions)if(s->staging.buffer)n+=s->staging.size;return n;}
 unsigned stagingHandles(){unsigned n=0;for(auto& s:e.submissions)n+=bool(s->staging.buffer);return n;}
 std::string state(){return "{\"resident_staging_payload\":"+std::to_string(residentStagingPayload())+",\"staging_handles\":"+std::to_string(stagingHandles())+",\"epoch\":"+std::to_string(epoch)+",\"epoch_bytes\":"+std::to_string(epochBytes)+",\"inflight_bytes\":"+std::to_string(inflightBytes)+",\"inflight_uploads\":"+std::to_string(inflight)+",\"accepted_uploads\":"+std::to_string(accepted)+",\"page_objects\":"+std::to_string(e.pages.size())+",\"live_pages\":"+std::to_string(e.livePages())+",\"submission_objects\":"+std::to_string(e.submissions.size())+",\"published\":"+std::to_string(e.publishedGeneration())+"}";}
};
int main(int argc,char**argv){try{
 if(argc!=5)throw std::runtime_error("SHADERS ATLAS VERTICES NEWOUT");auto mask=read(argv[2]),verts=read(argv[3]);if(verts.size()!=72)throw std::runtime_error("vertices size");for(size_t i=0;i<verts.size();i+=4)if(std::abs(verts[i])>4||std::abs(verts[i+1])>4||verts[i+2]<0||verts[i+2]>1||verts[i+3]<0||verts[i+3]>1)throw std::runtime_error("vertex bounds");std::filesystem::path out=argv[4];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");std::ofstream events(out/"events.jsonl");
 {TextLab v(argv[1]);if(!v.validation)throw std::runtime_error("validation required");Engine e(v);e.freeImage(v.coverage);Budget b(e);
 auto rejection=[&](const char* reason,auto fn){auto before=b.state();bool caught=false;try{fn();}catch(const std::runtime_error&x){if(std::string(x.what())!=reason)throw;caught=true;}if(!caught||before!=b.state())throw std::runtime_error("rejection modified state");events<<"{\"kind\":\"rejection\",\"reason\":\""<<reason<<"\",\"before\":"<<before<<",\"after\":"<<b.state()<<"}\n";};
 rejection("dimension_nonfinite",[&]{b.request(std::numeric_limits<double>::quiet_NaN(),49,mask,0);});rejection("dimension_invalid",[&]{b.request(-1,49,mask,0);});rejection("payload_overflow",[&]{b.request(UINT32_MAX,UINT32_MAX,mask,0);});rejection("extent_unsupported",[&]{b.request(66,49,mask,0);});auto shortMask=mask;shortMask.pop_back();rejection("mask_size",[&]{b.request(65,49,shortMask,0);});auto badMask=mask;badMask[0]=std::numeric_limits<float>::quiet_NaN();rejection("mask_nonfinite_or_range",[&]{b.request(65,49,badMask,0);});
 auto* current=&b.request(65,49,mask,0);e.wait(*b.upload);b.complete();if(!e.publish(*current))throw std::runtime_error("initial publish");
 for(int cycle=0;cycle<3;cycle++){
  b.nextEpoch(cycle*2+1);auto& old=e.drawPublished(verts,cycle+1);auto canceledMask=mask;for(auto& x:canceledMask)x*=.25f;auto& candidate=b.request(65,49,canceledMask,cycle*2+1);
  if(vkGetFenceStatus(v.device,old.fence)!=VK_NOT_READY||vkGetFenceStatus(v.device,b.upload->fence)!=VK_NOT_READY)throw std::runtime_error("expected pending");
  rejection("epoch_byte_limit",[&]{b.request(65,49,mask,cycle*2+2);});e.cancel(candidate);if(e.publish(candidate))throw std::runtime_error("canceled published");rejection("upload_not_complete",[&]{b.complete();});
  b.nextEpoch(cycle*2+2);rejection("inflight_upload_limit",[&]{b.request(65,49,mask,cycle*2+2);});
  events<<"{\"kind\":\"cancel_pending\",\"cycle\":"<<cycle<<",\"state\":"<<b.state()<<"}\n";
  e.signal(cycle+1);e.wait(old);e.wait(*b.upload);dump(old,out/("old-"+std::to_string(cycle)));b.releaseSubmission(old);b.complete();b.retire(candidate);
  auto newMask=mask;float factor=cycle%2?1.f:.5f;for(auto& x:newMask)x*=factor;auto* newer=&b.request(65,49,newMask,cycle*2+2);e.wait(*b.upload);b.complete();if(!e.publish(*newer))throw std::runtime_error("new publish");auto& fresh=e.drawPublished(verts);e.wait(fresh);dump(fresh,out/("new-"+std::to_string(cycle)));b.releaseSubmission(fresh);b.retire(*current);current=newer;
  rejection("epoch_byte_limit",[&]{b.request(65,49,mask,cycle*2+3);});
  if(b.inflight||b.inflightBytes||b.epochBytes!=Budget::capacity||e.pages.size()!=1||e.livePages()!=1||!e.submissions.empty())throw std::runtime_error("steady state mismatch");events<<"{\"kind\":\"steady\",\"cycle\":"<<cycle<<",\"state\":"<<b.state()<<"}\n";
 }
 if(b.accepted!=7)throw std::runtime_error("upload count");
 }
 if(validationErrors)throw std::runtime_error("validation");std::cout<<"UPLOAD_BUDGET_PASS validation_enabled=1 cycles=3\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
