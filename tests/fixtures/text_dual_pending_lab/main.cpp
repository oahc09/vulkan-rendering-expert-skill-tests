// SPDX-License-Identifier: MIT
#include "dual_pending.hpp"
int main(int argc,char**argv){try{
 if(argc!=5)throw std::runtime_error("SHADERS ATLAS VERTICES NEWOUT");const auto mask=read(argv[2]),vertices=read(argv[3]);const auto savedMask=mask,savedVertices=vertices;
 if(mask.size()!=3185||vertices.size()!=72)throw std::runtime_error("controlled input size");for(float x:mask)if(x<0||x>1)throw std::runtime_error("mask range");for(size_t i=0;i<vertices.size();i+=4)if(std::abs(vertices[i])>4||std::abs(vertices[i+1])>4||vertices[i+2]<0||vertices[i+2]>1||vertices[i+3]<0||vertices[i+3]>1)throw std::runtime_error("vertex bounds");
 std::filesystem::path out=argv[4];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");std::ofstream events(out/"events.jsonl");unsigned bComplete=0;
 {
 auto av=std::make_unique<TextLab>(argv[1]);auto ae=std::make_unique<Engine>(*av);TextLab bv(argv[1]);Engine be(bv);
 if(!av->validation||!bv.validation||av->device==bv.device)throw std::runtime_error("independent validated devices required");
 ae->freeImage(av->coverage);be.freeImage(bv.coverage);
 auto& ap=ae->page(0);auto& au=ae->upload(ap,mask);ae->wait(au);if(!ae->publish(ap))throw std::runtime_error("A publish");auto& ad=ae->drawPublished(vertices,1);
 auto pending=[&](){if(vkGetFenceStatus(av->device,ad.fence)!=VK_NOT_READY)throw std::runtime_error("A unexpectedly completed");uint64_t value=99;VK(vkGetSemaphoreCounterValue(av->device,ae->gate,&value));if(value!=0)throw std::runtime_error("A gate changed");};
 auto event=[&](const char*phase,bool aPending){events<<"{\"phase\":\""<<phase<<"\",\"A_pending\":"<<(aPending?"true":"false")<<",\"B_completed_renders\":"<<bComplete<<",\"B_published_generation\":"<<be.publishedGeneration()<<"}\n";};
 pending();event("A_gated",true);
 if(be.publish(ap))throw std::runtime_error("foreign publication allowed");bool foreignRejected=false;try{be.draw(ap,vertices);}catch(const std::runtime_error&e){if(std::string(e.what())!="foreign device page")throw;foreignRejected=true;}if(!foreignRejected)throw std::runtime_error("foreign draw allowed");
 auto& bp=be.page(0);auto& bu=be.upload(bp,mask);be.wait(bu);if(!be.publish(bp))throw std::runtime_error("B initial publish");auto& bd=be.drawPublished(vertices);be.wait(bd);++bComplete;dump(bd,out/"B-initial-A-pending");pending();event("B_initial_completed_A_pending",true);
 auto& canceled=be.page(1);auto cm=mask;for(auto& x:cm)x*=.25f;auto& cu=be.upload(canceled,cm);be.wait(cu);be.cancel(canceled);if(be.publish(canceled))throw std::runtime_error("B canceled publication");auto& wrong=be.draw(canceled,vertices);be.wait(wrong);++bComplete;dump(wrong,out/"B-wrong-canceled-route");be.retire(canceled);pending();event("B_candidate_canceled_A_pending",true);
 auto& next=be.page(2);auto nm=mask;for(auto& x:nm)x*=.5f;auto& nu=be.upload(next,nm);be.wait(nu);if(!be.publish(next)||be.publish(bp))throw std::runtime_error("B generation route guard");auto& nd=be.drawPublished(vertices);be.wait(nd);++bComplete;dump(nd,out/"B-new-A-pending");pending();event("B_new_completed_A_pending",true);
 // Fault while A is still genuinely gated. Engine destruction opens gate and
 // waits boundedly before destroying submitted resources; no simulated cancel.
 try{pending();throw std::runtime_error("CONTROLLED_A_PENDING_SCOPE_FAILURE");}
 catch(const std::runtime_error&e){if(std::string(e.what())!="CONTROLLED_A_PENDING_SCOPE_FAILURE")throw;ae.reset();av.reset();}
 if(validationErrors)throw std::runtime_error("A cleanup validation");event("A_pending_scope_cleaned",false);
 auto& continued=be.drawPublished(vertices);be.wait(continued);++bComplete;dump(continued,out/"B-after-A-destroyed");event("B_continued_after_A_destroyed",false);be.retire(bp);
 if(mask!=savedMask||vertices!=savedVertices)throw std::runtime_error("shared CPU input mutated");
 }
 if(validationErrors)throw std::runtime_error("final validation");events<<"{\"phase\":\"all_destroyed\",\"B_completed_renders\":"<<bComplete<<"}\n";
 std::cout<<"DUAL_PENDING_PASS validation_enabled=1 devices=2 A_gated_before_B_completion=1\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
