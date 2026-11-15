"""Adapt existing validated resource helper, fail closed on hook drift."""
from pathlib import Path

def prepare(build,fixtures):
 def replace(s,a,b):
  if s.count(a)!=1:raise ValueError('helper hook drift '+a)
  return s.replace(a,b)
 engine=build/'combined_engine.hpp';s=engine.read_text();s=replace(s,'enabled.multiDrawIndirect = mdi;','enabled.multiDrawIndirect = mdi;if(!f2.features.independentBlend)throw std::runtime_error("independentBlend unavailable");enabled.independentBlend=VK_TRUE;');engine.write_text(s)
 p=build/'combined_pipeline.hpp';s=p.read_text();s=replace(s,'VkAttachmentReference refs[3]={{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED},{VK_ATTACHMENT_UNUSED,VK_IMAGE_LAYOUT_UNDEFINED}};','VkAttachmentReference refs[3]={{0,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{1,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},{2,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL}};');s=replace(s,'sub.preserveAttachmentCount=2;sub.pPreserveAttachments=preserved;','sub.preserveAttachmentCount=0;sub.pPreserveAttachments=nullptr;');s=replace(s,'VkPipelineColorBlendStateCreateInfo bs{','for(int i=1;i<3;i++){blends[i].blendEnable=VK_FALSE;blends[i].colorWriteMask=BAD_WRITE?15:0;}VkPipelineColorBlendStateCreateInfo bs{');p.write_text('#ifndef BAD_WRITE\n#define BAD_WRITE 0\n#endif\n'+s)
 s=(fixtures/'text_combined_lifecycle_lab/main.cpp').read_text();marker='int main(int argc,char**argv)'
 if s.count(marker)!=1:raise ValueError('main hook')
 s=s[:s.index(marker)];s=replace(s,'SubmissionResources& begin(){auto s=', 'SubmissionResources& begin(){if(submissions.size()>=3)throw std::runtime_error("submission capacity");auto s=')
 s=replace(s,'struct PageResources {Image image{};','struct PageResources {VkDevice owner{};Image image{};');s=replace(s,'struct SubmissionResources {VkCommandBuffer cb{};','struct SubmissionResources {std::vector<PageResources*> refs;VkCommandBuffer cb{};');s=replace(s,'p->generation=gen;','p->generation=gen;p->owner=v.device;')
 s=replace(s,'for(auto& s:submissions)if(s->pending)throw std::runtime_error("page retirement with pending consumers");','for(auto& s:submissions)if(s->pending&&std::find(s->refs.begin(),s->refs.end(),&p)!=s->refs.end())throw std::runtime_error("page retirement with pending consumers");')
 for op in ('retire','cancel'):s=replace(s,'void '+op+'(PageResources& p){','void '+op+'(PageResources& p){if(p.owner!=v.device)throw std::runtime_error("foreign page");')
 s=replace(s,'const std::vector<float>& mask){auto& s=begin();','const std::vector<float>& mask){if(p.owner!=v.device||!p.live)throw std::runtime_error("invalid upload page");auto& s=begin();s.refs={&p};')
 start=s.index(' SubmissionResources& draw(PageResources& p,');end=s.index(' ~Engine()',start)
 draw=s[start:end]
 draw=replace(draw,'SubmissionResources& draw(PageResources& p,const std::vector<float>& vertices,uint64_t gateValue=0)','SubmissionResources& drawBatch(const std::vector<PageResources*>& pages,const std::vector<unsigned>& counts,const std::vector<float>& vertices,uint64_t gateValue=0)')
 draw=replace(draw,'if(!p.live)throw std::runtime_error("dead page route");auto& s=begin();','if(pages.empty()||pages.size()>2||pages.size()!=counts.size())throw std::runtime_error("batch count");size_t total=0;for(size_t i=0;i<pages.size();i++){auto* p=pages[i];if(!p||p->owner!=v.device||!p->live||!p->uploadComplete)throw std::runtime_error("invalid batch page");if(!counts[i]||counts[i]>48||counts[i]%6)throw std::runtime_error("vertex count");total+=counts[i];}if(vertices.size()!=total*4)throw std::runtime_error("vertex size");auto& s=begin();s.refs=pages;')
 draw=replace(draw,'vkCmdBindDescriptorSets(s.cb,VK_PIPELINE_BIND_POINT_GRAPHICS,v.textLayout,0,1,&p.set,0,nullptr);','')
 draw=replace(draw,'vkCmdDraw(s.cb,vertices.size()/4,1,0,0);','unsigned first=0;for(size_t i=0;i<pages.size();i++){vkCmdBindDescriptorSets(s.cb,VK_PIPELINE_BIND_POINT_GRAPHICS,v.textLayout,0,1,&pages[i]->set,0,nullptr);vkCmdDraw(s.cb,counts[i],1,first,0);first+=counts[i];}')
 s=s[:end]+draw+s[end:]
 # Legacy helper methods remain unused in service, keep old draw valid and tracked.
 s=replace(s,'if(!p.live)throw std::runtime_error("dead page route");auto& s=begin();','if(p.owner!=v.device||!p.live)throw std::runtime_error("dead page route");auto& s=begin();s.refs={&p};')
 (build/'service.hpp').write_text(s)
