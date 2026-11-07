// SPDX-License-Identifier: MIT
// Small numerical fixtures, not a production solver. Reuse Engine Scale device,
// allocations, command recording, fence, graphics pipeline, and image readback.
#define main engine_scale_lab_original_main
#include "../engine_scale_lab/main.cpp"
#undef main
#include <iomanip>
#include <set>
struct Particle { float x[4], previous[4]; };
struct Edge { uint32_t a,b; float rest,compliance; };
static_assert(sizeof(Particle)==32 && sizeof(Edge)==16,"std430 ABI");
using V3=std::array<double,3>;
struct Ref { V3 x,previous; double w; };
static V3 add(V3 a,V3 b){for(int c=0;c<3;c++)a[c]+=b[c];return a;}
static V3 sub(V3 a,V3 b){for(int c=0;c<3;c++)a[c]-=b[c];return a;}
static V3 mul(V3 a,double s){for(auto &v:a)v*=s;return a;}
static double norm(V3 a){return std::sqrt(a[0]*a[0]+a[1]*a[1]+a[2]*a[2]);}
static V3 cross(V3 a,V3 b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
static void require(bool ok,const std::string &message){if(!ok)throw std::runtime_error(message);}
static std::vector<Ref> reference(const std::vector<Particle>&p){std::vector<Ref> r;for(auto q:p)r.push_back({{q.x[0],q.x[1],q.x[2]},{q.previous[0],q.previous[1],q.previous[2]},q.x[3]});return r;}
static std::vector<std::pair<uint32_t,uint32_t>> colorEdges(std::vector<Edge>& edges){
 std::vector<std::vector<Edge>> colors;std::vector<std::set<uint32_t>> used;
 for(auto e:edges){size_t c=0;while(c<used.size()&&(used[c].count(e.a)||used[c].count(e.b)))c++;if(c==used.size()){used.emplace_back();colors.emplace_back();}used[c].insert(e.a);used[c].insert(e.b);colors[c].push_back(e);}
 edges.clear();std::vector<std::pair<uint32_t,uint32_t>> ranges;
 for(auto &c:colors){ranges.emplace_back(edges.size(),c.size());std::set<uint32_t> writes;for(auto e:c){require(writes.insert(e.a).second&&writes.insert(e.b).second,"color write conflict");edges.push_back(e);}}
 return ranges;
}
static void solveCPU(std::vector<Ref>&s,const std::vector<Edge>&edges,std::vector<double>&lambda,double h,bool jacobi){
 std::vector<V3> contributions(s.size(),V3{});
 for(size_t i=0;i<edges.size();i++){auto e=edges[i];auto d=sub(s[e.b].x,s[e.a].x);double len=norm(d),a=e.compliance/(h*h),den=s[e.a].w+s[e.b].w+a;if(len<1e-8||den<=0)continue;
  double dl=(-(len-e.rest)-a*lambda[i])/den;lambda[i]+=dl;auto da=mul(d,-s[e.a].w*dl/len),db=mul(d,s[e.b].w*dl/len);
  if(jacobi){contributions[e.a]=add(contributions[e.a],da);contributions[e.b]=add(contributions[e.b],db);}else{s[e.a].x=add(s[e.a].x,da);s[e.b].x=add(s[e.b].x,db);}}
 if(jacobi)for(size_t i=0;i<s.size();i++)s[i].x=add(s[i].x,contributions[i]);
}
static void collideCPU(std::vector<Ref>&s,uint32_t kind){for(auto &q:s)if(q.w){q.x[1]=std::max(q.x[1],-.55);V3 center={kind==2?std::clamp(q.x[0],-.18,.18):0.,-.2,0.};auto d=sub(q.x,center);double l=norm(d);if(l<.14)q.x=add(center,mul(l<1e-8?V3{0,1,0}:mul(d,1/l),.14));}}
struct Simulation {
 Vulkan v; VkPipeline integrate,reset,solve,gather,collision,publish,wave,bounds,inject;
 std::filesystem::path out;uint32_t caseCount=0,drawCount=0,dispatches=0;double maximumError=0;
 std::chrono::steady_clock::time_point cpuStart;
 void timing(const std::string&name,uint32_t count){
  double cpuMs=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-cpuStart).count();
  std::ofstream f(out/"timings.jsonl",std::ios::app);f<<std::setprecision(17)<<"{\"phase\":\""<<name<<"\",\"cpu_record_submit_wait_ms\":"<<cpuMs<<",\"dispatches\":"<<dispatches<<",\"timestamp_valid_bits\":"<<v.timestampBits<<",\"timestamp_period_ns\":"<<v.properties.limits.timestampPeriod<<",\"gpu_stage_ms\":[";
  if(v.timestamps){uint64_t q[4]{};VK(vkGetQueryPoolResults(v.device,v.queries,0,count,sizeof(q),q,8,VK_QUERY_RESULT_64_BIT));uint64_t mask=v.timestampBits==64?UINT64_MAX:(uint64_t(1)<<v.timestampBits)-1;for(uint32_t i=1;i<count;i++){if(i>1)f<<',';f<<((q[i]-q[i-1])&mask)*v.properties.limits.timestampPeriod/1e6;}}
  f<<"],\"gpu_stage_names\":"<<(name=="tick"?"[\"simulate\",\"normal_bounds\"]":"[\"draw\",\"image_readback\"]")<<",\"hardware_performance_claim\":false}\n";
 }

 Simulation(const std::string&shaders,const std::filesystem::path&target):v(4096,shaders,true),out(target){
  require(v.properties.limits.maxComputeWorkGroupInvocations>=64&&v.properties.limits.maxComputeWorkGroupSize[0]>=64&&v.properties.limits.maxComputeSharedMemorySize>=1536&&v.properties.limits.maxStorageBufferRange>=4096*32,"simulation limits unavailable");
  // Larger independent scratch/normal resources share the established layout.
  replace(3,32);replace(5,4096*32);replace(7,4096*16);
  integrate=v.compute("integrate.comp");reset=v.compute("reset_lambda.comp");solve=v.compute("solve.comp");gather=v.compute("gather.comp");collision=v.compute("collision.comp");publish=v.compute("publish.comp");wave=v.compute("wave.comp");bounds=v.compute("bounds.comp");inject=v.compute("inject.comp");
 }
 void replace(uint32_t binding,size_t bytes){auto b=v.buffer(bytes,VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);v.buffers.push_back(b);VkDescriptorBufferInfo info{b.buffer,0,b.size};VkWriteDescriptorSet w{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};w.dstSet=v.set;w.dstBinding=binding;w.descriptorCount=1;w.descriptorType=VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;w.pBufferInfo=&info;vkUpdateDescriptorSets(v.device,1,&w,0,nullptr);}
 Buffer& normalBuffer(){return v.buffers[11];}Buffer& boundBuffer(){return v.buffers[9];}
 void dependency(){v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT);}
 void dispatch(VkPipeline pipeline,Push p,uint32_t count){v.bindCompute(pipeline,p,(count+63)/64);dispatches++;dependency();}
 void begin(){cpuStart=std::chrono::steady_clock::now();dispatches=0;v.begin();if(v.timestamps)vkCmdResetQueryPool(v.cb,v.queries,0,3);v.stamp(0);v.barrier(VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_WRITE_BIT,VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT|VK_ACCESS_SHADER_WRITE_BIT);}
 void finish(){v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);v.stamp(2);v.submit();timing("tick",3);}
 void initialize(const std::vector<Particle>&particles,const std::vector<Edge>&edges){require(particles.size()<=4096&&edges.size()<=4096,"capacity exceeded");std::memcpy(v.buffers[0].map,particles.data(),particles.size()*sizeof(Particle));std::memcpy(v.buffers[1].map,particles.data(),particles.size()*sizeof(Particle));if(!edges.empty())std::memcpy(v.buffers[2].map,edges.data(),edges.size()*sizeof(Edge));}
 void snapshot(Push p){v.stamp(1);dispatch(publish,p,p.n);v.bindCompute(bounds,p,1);dispatches++;dependency();}
 void draw(const std::string&name,Push p){
  cpuStart=std::chrono::steady_clock::now();dispatches=0;v.begin();if(v.timestamps)vkCmdResetQueryPool(v.cb,v.queries,0,3);v.stamp(0);v.barrier(VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT,VK_ACCESS_SHADER_WRITE_BIT,VK_PIPELINE_STAGE_VERTEX_SHADER_BIT,VK_ACCESS_SHADER_READ_BIT);
  // This intentionally serialized baseline waits on every consumer fence. No
  // asynchronous or three-frames-in-flight lifetime proof is claimed.
  v.barrier(VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,VK_ACCESS_MEMORY_WRITE_BIT|VK_ACCESS_MEMORY_READ_BIT,VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,VK_ACCESS_MEMORY_WRITE_BIT|VK_ACCESS_MEMORY_READ_BIT);
  v.startPass(false);vkCmdBindPipeline(v.cb,VK_PIPELINE_BIND_POINT_GRAPHICS,v.graphics);v.push(p);
  if(p.mode==2)vkCmdDraw(v.cb,(p.width-1)*(p.height-1)*6,1,0,0);else vkCmdDraw(v.cb,6,p.n,0,0);
  vkCmdEndRenderPass(v.cb);v.stamp(1);v.transition(v.color,VK_IMAGE_ASPECT_COLOR_BIT,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_READ_BIT);
  v.copyImage(v.color,VK_IMAGE_ASPECT_COLOR_BIT,v.buffers[7]);v.barrier(VK_PIPELINE_STAGE_TRANSFER_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_HOST_BIT,VK_ACCESS_HOST_READ_BIT);v.stamp(2);v.submit();timing("draw",3);
  auto pixels=(uint8_t*)v.buffers[7].map;std::ofstream raw(out/(name+".rgba"),std::ios::binary);raw.write((char*)pixels,v.width*v.height*4);
  uint32_t coverage=0;std::ofstream ppm(out/(name+".ppm"),std::ios::binary);ppm<<"P6\n"<<v.width<<" "<<v.height<<"\n255\n";
  for(uint32_t i=0;i<v.width*v.height;i++){ppm.write((char*)(pixels+4*i),3);coverage+=pixels[4*i]||pixels[4*i+1]||pixels[4*i+2];}
  require(coverage>0,"empty geometry render");drawCount++;
 }
 void check(const std::string&name,const std::vector<Ref>&cpu,Push p,double tolerance,bool water=false){
  auto gpu=(Particle*)v.buffers[0].map;auto normals=(float*)normalBuffer().map;auto box=(float*)boundBuffer().map;
  V3 lo={1e30,1e30,1e30},hi={-1e30,-1e30,-1e30};double error=0,normalError=0;std::vector<V3> expectedNormals;
  std::ofstream f(out/(name+".json"));f<<std::setprecision(17)<<"{\"name\":\""<<name<<"\",\"tolerance\":"<<tolerance<<",\"normal_tolerance\":0.00005,\"tick\":"<<p.tick<<",\"gpu\":[";
  for(size_t i=0;i<cpu.size();i++){
   if(i){f<<',';}f<<'[';
   for(int c=0;c<3;c++){require(std::isfinite(gpu[i].x[c])&&std::isfinite(cpu[i].x[c]),"nonfinite state");error=std::max(error,std::abs(gpu[i].x[c]-cpu[i].x[c]));if(c)f<<',';f<<gpu[i].x[c];}
   f<<']';V3 pos=cpu[i].x;if(water)pos={double(i%p.width)/(p.width-1),double(i/p.width)/(p.height-1),cpu[i].x[0]};for(int c=0;c<3;c++){lo[c]=std::min(lo[c],pos[c]);hi[c]=std::max(hi[c],pos[c]);}
   uint32_t x=i%p.width,y=i/p.width,l=y*p.width+(x?x-1:x),r=y*p.width+std::min(x+1,p.width-1),d=(y?y-1:y)*p.width+x,u=std::min(y+1,p.height-1)*p.width+x;V3 n={0,0,1};
   if(water)n={-(cpu[r].x[0]-cpu[l].x[0])/(r-l)*(p.width-1),-(cpu[u].x[0]-cpu[d].x[0])/((u-d)/p.width)*(p.height-1),1};
   else if(p.height>1)n=cross(sub(cpu[r].x,cpu[l].x),sub(cpu[u].x,cpu[d].x));
   if(norm(n)>1e-8)n=mul(n,1/norm(n));else n={0,0,1};
   expectedNormals.push_back(n);for(int c=0;c<3;c++){require(std::isfinite(normals[i*4+c]),"nonfinite normal");normalError=std::max(normalError,std::abs(normals[i*4+c]-n[c]));}
   require(normals[i*4+3]==p.tick,"normal generation mismatch");
  }
  f<<"],\"cpu\":[";for(size_t i=0;i<cpu.size();i++){if(i)f<<',';f<<'['<<cpu[i].x[0]<<','<<cpu[i].x[1]<<','<<cpu[i].x[2]<<']';}
  f<<"],\"normals\":[";for(size_t i=0;i<cpu.size();i++){if(i)f<<',';f<<'['<<normals[4*i]<<','<<normals[4*i+1]<<','<<normals[4*i+2]<<','<<normals[4*i+3]<<']';}
  f<<"],\"cpu_normals\":[";for(size_t i=0;i<cpu.size();i++){if(i)f<<',';f<<'['<<expectedNormals[i][0]<<','<<expectedNormals[i][1]<<','<<expectedNormals[i][2]<<']';}
  f<<"],\"cpu_bounds\":["<<lo[0]<<','<<lo[1]<<','<<lo[2]<<','<<p.tick<<','<<hi[0]<<','<<hi[1]<<','<<hi[2]<<','<<p.tick;
  f<<"],\"max_error\":"<<error<<",\"normal_max_error\":"<<normalError<<",\"bounds\":[";for(int c=0;c<8;c++){if(c)f<<',';f<<box[c];}f<<"]}\n";
  require(error<=tolerance,"CPU/GPU numerical mismatch in "+name);require(normalError<=5e-5,"CPU/GPU normal mismatch in "+name);
  for(int c=0;c<3;c++){require(std::isfinite(box[c])&&std::isfinite(box[c+4]),"nonfinite bounds");require(std::abs(box[c]-lo[c])<=tolerance&&std::abs(box[c+4]-hi[c])<=tolerance,"bounds mismatch");}
  require(box[3]==p.tick&&box[7]==p.tick,"bounds generation mismatch");maximumError=std::max(maximumError,error);caseCount++;
 }

 void constraintCheck(const std::string&name,const std::vector<Ref>&cpu,const std::vector<Edge>&edges,const std::vector<double>&lambda,Push p){
  auto gpu=(Particle*)v.buffers[0].map;auto gl=(float*)v.buffers[4].map;double residualDifference=0,maxResidual=0,lambdaError=0,penetration=0,fixedError=0;
  std::ofstream f(out/(name+"-constraints.json"));f<<std::setprecision(17)<<"{\"residual_difference_tolerance\":0.0001,\"lambda_tolerance\":0.00005,\"penetration_tolerance\":0.00001,\"fixed_tolerance\":0,\"edges\":[";
  for(size_t i=0;i<edges.size();i++){auto e=edges[i];V3 ga={gpu[e.a].x[0],gpu[e.a].x[1],gpu[e.a].x[2]},gb={gpu[e.b].x[0],gpu[e.b].x[1],gpu[e.b].x[2]};double cr=norm(sub(cpu[e.a].x,cpu[e.b].x))-e.rest,gr=norm(sub(ga,gb))-e.rest;residualDifference=std::max(residualDifference,std::abs(cr-gr));maxResidual=std::max(maxResidual,std::abs(gr));lambdaError=std::max(lambdaError,std::abs(lambda[i]-gl[i]));if(i)f<<',';f<<'['<<e.a<<','<<e.b<<','<<e.rest<<','<<cr<<','<<gr<<','<<lambda[i]<<','<<gl[i]<<']';}
  for(size_t i=0;i<cpu.size();i++){V3 g={gpu[i].x[0],gpu[i].x[1],gpu[i].x[2]};if(cpu[i].w==0)fixedError=std::max(fixedError,norm(sub(g,cpu[i].x)));else {V3 center={p.flags==2?std::clamp(g[0],-.18,.18):0.,-.2,0.};penetration=std::max({penetration,-.55-g[1],.14-norm(sub(g,center))});}}
  f<<"],\"max_residual_difference\":"<<residualDifference<<",\"max_absolute_residual_observed\":"<<maxResidual<<",\"max_lambda_error\":"<<lambdaError<<",\"max_discrete_penetration\":"<<penetration<<",\"max_fixed_error\":"<<fixedError<<"}\n";
  require(residualDifference<=1e-4&&lambdaError<=5e-5&&penetration<=1e-5&&fixedError==0,"constraint metric mismatch");
 }
 void distance(bool soft,bool jacobi){std::vector<Particle> particles={{{0,0,0,0},{0,0,0,0}},{{1.2f,0,0,1},{1.2f,0,0,0}}};std::vector<Edge> edges={{0,1,1,soft?.01f:0.f}};auto cpu=reference(particles);std::vector<double> lambda(1);initialize(particles,edges);Push p{};p.n=2;p.width=2;p.height=1;p.capacity=p.level=1;p.viewX=.1f;p.mode=jacobi;p.tick=1;
  begin();dispatch(reset,p,1);for(int iteration=0;iteration<3;iteration++){dispatch(solve,p,1);if(jacobi)dispatch(gather,p,2);solveCPU(cpu,edges,lambda,p.viewX,jacobi);}snapshot(p);finish();
  require(std::abs(((Particle*)v.buffers[0].map)[1].x[0]-(soft?1.1:1.))<1e-5,"scalar XPBD oracle mismatch");
  require(std::abs(((float*)v.buffers[4].map)[0]-lambda[0])<1e-5,"lambda accumulation mismatch");check(std::string(soft?"soft":"hard")+(jacobi?"-jacobi":"-colored"),cpu,p,1e-5);
 }
 void deform(bool cloth,bool jacobi){uint32_t width=cloth?8:32,height=cloth?8:1;std::vector<Particle> particles;std::vector<Edge> edges;
  for(uint32_t y=0;y<height;y++)for(uint32_t x=0;x<width;x++){float px=cloth?-.42f+.12f*x:-.62f+.04f*x,py=cloth?.45f-.12f*y:.12f;float w=cloth?(y==0&& (x==0||x==width-1)?0:1):(x==0?0:1);particles.push_back({{px,py,0,w},{px,py,0,0}});}
  auto edge=[&](uint32_t a,uint32_t b){auto x=particles[a].x,y=particles[b].x;float dx=x[0]-y[0],dy=x[1]-y[1];edges.push_back({a,b,std::sqrt(dx*dx+dy*dy),cloth?.01f:.0001f});};
  for(uint32_t y=0;y<height;y++)for(uint32_t x=0;x<width;x++){uint32_t i=y*width+x;if(x+1<width)edge(i,i+1);if(y+1<height)edge(i,i+width);if(cloth&&x+1<width&&y+1<height){edge(i,i+width+1);edge(i+1,i+width);}if(cloth&&x+2<width)edge(i,i+2);if(cloth&&y+2<height)edge(i,i+2*width);}
  auto ranges=colorEdges(edges);auto cpu=reference(particles);initialize(particles,edges);Push p{};p.n=particles.size();p.width=width;p.height=height;p.capacity=edges.size();p.viewX=.01f;p.mode=jacobi;p.flags=cloth?2:1;
  for(uint32_t tick=1;tick<=8;tick++){p.tick=tick;
   // A prescribed moving anchor, not mass-zero velocity guessed by the solver.
   // CPU and GPU use the identical FP32 input; prior consumer fences completed.
   if(cloth){float target=particles[0].x[0]+.002f*float(tick);cpu[0].x[0]=target;((Particle*)v.buffers[0].map)[0].x[0]=target;}
   std::vector<double> lambda(edges.size());for(auto &q:cpu){auto old=q.x;if(q.w)q.x=add(add(q.x,sub(q.x,q.previous)),V3{0,-.1*p.viewX*p.viewX,0});q.previous=old;}
   begin();dispatch(integrate,p,p.n);dispatch(reset,p,p.capacity);
   for(int iteration=0;iteration<3;iteration++){if(jacobi){p.base=0;p.level=p.capacity;dispatch(solve,p,p.capacity);dispatch(gather,p,p.n);}else for(auto range:ranges){p.base=range.first;p.level=range.second;dispatch(solve,p,p.level);}solveCPU(cpu,edges,lambda,p.viewX,jacobi);}
   dispatch(collision,p,p.n);collideCPU(cpu,p.flags);snapshot(p);finish();
   std::string name=(cloth?"cloth":"rope")+std::string(jacobi?"-jacobi":"-colored")+"-tick"+std::to_string(tick);check(name,cpu,p,5e-5);constraintCheck(name,cpu,edges,lambda,p);
   if(tick==1||tick==8){auto before=std::vector<Particle>((Particle*)v.buffers[0].map,(Particle*)v.buffers[0].map+p.n);p.zoom=0;draw(name+"-view0",p);p.zoom=.06f;draw(name+"-view1",p);require(std::memcmp(before.data(),v.buffers[0].map,p.n*sizeof(Particle))==0,"consumer advanced simulation");}
  }
 }
 void water(uint32_t size,uint32_t boundary,uint32_t eventMode){uint32_t n=size*size;std::vector<Particle> particles(n);std::vector<Edge> events;if(eventMode){events.push_back({n/2,0,.4f,0});if(eventMode>=2){events.push_back({n/2,0,.2f,0});events.push_back({n/2+1,2,.1f,0});}if(eventMode==3)for(uint32_t i=0;i<128;i++)events.push_back({(i*7)%n,i%4,.001f,0});}auto cpu=reference(particles);initialize(particles,events);Push p{};p.n=n;p.width=p.height=size;p.mode=2;p.flags=boundary;p.viewX=.01f;p.zoom=.5f;p.capacity=events.size();
  double r=p.zoom*p.viewX*std::sqrt(2.*(size-1)*(size-1));require(r<=.9,"CFL safety margin exceeded");
  for(uint32_t tick=0;tick<12;tick++){p.tick=tick;for(auto e:events)if(e.b==tick)cpu[e.a].x[1]+=e.rest;auto next=cpu;auto sample=[&](int x,int y){return cpu[std::clamp(y,0,int(size)-1)*size+std::clamp(x,0,int(size)-1)].x[0];};
   for(uint32_t y=0;y<size;y++)for(uint32_t x=0;x<size;x++){uint32_t i=y*size+x;double z=cpu[i].x[0],velocity=cpu[i].x[1],lap=(sample(x-1,y)+sample(x+1,y)+sample(x,y-1)+sample(x,y+1)-4*z)*(size-1)*(size-1);velocity+=p.viewX*p.zoom*p.zoom*lap;if(boundary==2){velocity/=1+.1*p.viewX;if(x==0||y==0||x==size-1||y==size-1)velocity*=.5;}z+=p.viewX*velocity;if(boundary==0&&(x==0||y==0||x==size-1||y==size-1))z=velocity=0;next[i].x={z,velocity,0};}
   cpu=next;
   begin();dispatch(inject,p,p.n);dispatch(wave,p,p.n);snapshot(p);finish();std::string name="wave-"+std::to_string(size)+"-"+std::to_string(boundary)+"-events"+std::to_string(eventMode)+"-tick"+std::to_string(tick);check(name,cpu,p,1e-5,true);
   if(tick==0||tick==11){auto simulationSpeed=p.zoom;p.zoom=0;draw(name+"-view0",p);p.zoom=.06f;draw(name+"-view1",p);p.zoom=simulationSpeed;}
  }
 }
};
int main(int argc,char**argv){try{
 require(argc==3,"usage: simulation_lab SHADER_DIR NEW_OUTPUT_DIR");std::filesystem::path out=argv[2];require(std::filesystem::create_directory(out),"Refuse existing output directory");
 Simulation s(argv[1],out);for(bool jacobi:{false,true}){s.distance(false,jacobi);s.distance(true,jacobi);s.deform(false,jacobi);s.deform(true,jacobi);}for(uint32_t boundary=0;boundary<3;boundary++){s.water(17,boundary,2);s.water(17,boundary,0);}s.water(17,1,1);s.water(17,1,3);s.water(9,1,2);
 require(validationErrors==0,"Vulkan validation errors");std::ofstream summary(out/"result.json");summary<<std::setprecision(17)<<"{\"status\":\"PASS\",\"numerical_cases\":"<<s.caseCount<<",\"draws\":"<<s.drawCount<<",\"max_position_or_velocity_error\":"<<s.maximumError<<",\"validation_available\":"<<s.v.validation<<",\"validation_errors\":"<<validationErrors<<",\"float_atomics_enabled\":false,\"scheduling\":\"single queue, synchronous fence per tick/consumer\",\"mobile_acceptance\":\"UNVERIFIED\"}\n";std::cout<<"Simulation Lab PASS "<<s.caseCount<<" cases, "<<s.drawCount<<" draws\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
