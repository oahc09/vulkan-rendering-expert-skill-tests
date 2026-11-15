// SPDX-License-Identifier: MIT
#include "combined_source.hpp"
static void releaseCompleted(Engine& e){
 for(auto& s:e.submissions){if(s->pending)throw std::runtime_error("release pending submission");if(s->fb)vkDestroyFramebuffer(e.v.device,s->fb,nullptr);e.freeImage(s->target);e.freeImage(s->velocity);e.freeImage(s->id);e.freeBuffer(s->staging);e.freeBuffer(s->vertices);e.freeBuffer(s->colorRead);e.freeBuffer(s->velocityRead);e.freeBuffer(s->idRead);vkDestroyFence(e.v.device,s->fence,nullptr);vkFreeCommandBuffers(e.v.device,e.v.pool,1,&s->cb);}
 for(auto& p:e.pages)p->uploadSubmission=nullptr;e.submissions.clear();
 e.pages.erase(std::remove_if(e.pages.begin(),e.pages.end(),[](auto& p){return !p->live;}),e.pages.end());
}
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("usage SHADERS INPUT NEW_OUT");std::filesystem::path input=argv[2],out=argv[3];
 std::vector<std::vector<float>> masks,vertices;
 for(int i=0;i<7;i++){auto dir=input/std::to_string(i);auto m=read((dir/"atlas.f32").c_str()),v=read((dir/"vertices.f32").c_str());if(m.size()!=3185||v.size()!=24)throw std::runtime_error("dimensions");for(float x:m)if(x<0||x>1)throw std::runtime_error("coverage");for(size_t k=0;k<v.size();k+=4)if(std::abs(v[k])>4||std::abs(v[k+1])>4||v[k+2]<0||v[k+2]>1||v[k+3]<0||v[k+3]>1)throw std::runtime_error("vertices");masks.push_back(m);vertices.push_back(v);}
 if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");
 {TextLab lab(argv[1]);Engine e(lab);e.freeImage(lab.coverage);auto* current=&e.page(0);auto& u=e.upload(*current,masks[0]);e.wait(u);if(!e.publish(*current))throw std::runtime_error("publish initial");releaseCompleted(e);std::ofstream events(out/"events.jsonl");
 for(int round=1;round<=6;round++){
  auto folder=out/std::to_string(round);std::filesystem::create_directory(folder);auto& old=e.drawPublished(vertices[round-1],round);auto& candidate=e.page(round*2-1);auto& upload=e.upload(candidate,masks[round]);
  if(vkGetFenceStatus(lab.device,old.fence)!=VK_NOT_READY||vkGetFenceStatus(lab.device,upload.fence)!=VK_NOT_READY)throw std::runtime_error("not pending");if(e.publish(candidate))throw std::runtime_error("pending publish");e.cancel(candidate);if(e.publish(candidate))throw std::runtime_error("cancel publish");bool rejected=false;try{e.retire(candidate);}catch(const std::runtime_error&){rejected=true;}if(!rejected)throw std::runtime_error("pending retire");
  events<<"{\"round\":"<<round<<",\"phase\":\"pending_cancel\",\"published\":"<<e.publishedGeneration()<<",\"live_pages\":"<<e.livePages()<<",\"pending\":2}\n";
  e.signal(round);e.wait(old);e.wait(upload);dump(old,folder/"old");if(e.publish(candidate))throw std::runtime_error("completed cancel publish");auto& retained=e.drawPublished(vertices[round-1]);e.wait(retained);dump(retained,folder/"retained");e.retire(candidate);releaseCompleted(e);
  auto& next=e.page(round*2);auto& nu=e.upload(next,masks[round]);e.wait(nu);if(!e.publish(next)||e.publish(*current))throw std::runtime_error("generation guard");auto& drawn=e.drawPublished(vertices[round]);e.wait(drawn);dump(drawn,folder/"new");e.retire(*current);current=&next;releaseCompleted(e);
  events<<"{\"round\":"<<round<<",\"phase\":\"retired\",\"published\":"<<e.publishedGeneration()<<",\"live_pages\":"<<e.livePages()<<",\"submission_resources\":"<<e.submissions.size()<<",\"page_objects\":"<<e.pages.size()<<"}\n";
 }
 std::cout<<"CONTENT_CHURN_PASS validation_enabled="<<lab.validation<<"\n";
 }if(validationErrors)throw std::runtime_error("validation errors");std::cout<<"CONTENT_CHURN_DESTROYED\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return validationErrors?2:1;}}
