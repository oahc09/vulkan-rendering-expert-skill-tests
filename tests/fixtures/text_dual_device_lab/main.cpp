// SPDX-License-Identifier: MIT
#include "dual_helper.hpp"
#include <memory>
struct Output {
 std::unique_ptr<TextLab> lab;bool paused=false;unsigned frames=0,generation=0;static unsigned live,created,destroyed;
 explicit Output(const std::string& shaders,unsigned gen):lab(std::make_unique<TextLab>(shaders)),generation(gen){if(!lab->validation)throw std::runtime_error("validation unavailable");++live;++created;}
 ~Output(){lab.reset();--live;++destroyed;}
 void render(const std::vector<float>& mask,const std::filesystem::path& dir){if(paused)throw std::runtime_error("output paused");if(!std::filesystem::create_directory(dir))throw std::runtime_error("existing frame");auto result=lab->draw(mask,{.1f,.2f,.3f,.5f},{.9f,.5f,.2f,.75f});save(dir/"color.rgba32f",result[0]);save(dir/"velocity.rgba32f",result[1]);save(dir/"id.rgba32f",result[2]);std::vector<float> depth(65*49);std::memcpy(depth.data(),lab->buffers[lab->readDepth].map,depth.size()*4);save(dir/"depth.f32",depth);++frames;}
};unsigned Output::live=0;unsigned Output::created=0;unsigned Output::destroyed=0;
static std::vector<float> read(const std::filesystem::path& p){std::ifstream f(p,std::ios::binary|std::ios::ate);if(!f||f.tellg()!=65*49*4)throw std::runtime_error("mask size");std::vector<float>m(65*49);f.seekg(0);f.read((char*)m.data(),m.size()*4);for(float x:m)if(!std::isfinite(x)||x<0||x>1)throw std::runtime_error("mask range");return m;}
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("SHADERS MASK_DIR NEWOUT");const std::array<std::vector<float>,3> masks={read(std::filesystem::path(argv[2])/"0.f32"),read(std::filesystem::path(argv[2])/"1.f32"),read(std::filesystem::path(argv[2])/"2.f32")};const auto saved=masks;
 std::filesystem::path out=argv[3];if(!std::filesystem::create_directory(out))throw std::runtime_error("existing output");std::ofstream events(out/"events.jsonl");
 {auto a=std::make_unique<Output>(argv[1],0);auto b=std::make_unique<Output>(argv[1],0);if(a->lab->device==b->lab->device)throw std::runtime_error("devices aliased");
 auto event=[&](const char* phase){events<<"{\"phase\":\""<<phase<<"\",\"live\":"<<Output::live<<",\"created\":"<<Output::created<<",\"destroyed\":"<<Output::destroyed<<",\"A_frames\":"<<(a?a->frames:0)<<",\"B_frames\":"<<b->frames<<",\"A_generation\":"<<(a?int(a->generation):-1)<<"}\n";};
 a->render(masks[0],out/"A-initial");b->render(masks[0],out/"B-initial");event("both_created");
 a->paused=true;bool rejected=false;try{a->render(masks[1],out/"paused-invalid");}catch(const std::runtime_error& e){if(std::string(e.what())!="output paused")throw;rejected=true;}if(!rejected||a->frames!=1||std::filesystem::exists(out/"paused-invalid"))throw std::runtime_error("paused output executed");b->render(masks[1],out/"B-A-paused");event("A_paused_B_rendered");
 a.reset();b->render(masks[2],out/"B-A-destroyed");event("A_destroyed_B_rendered");
 a=std::make_unique<Output>(argv[1],1);if(a->lab->device==b->lab->device)throw std::runtime_error("rebuilt devices aliased");a->render(masks[2],out/"A-rebuilt");b->render(masks[0],out/"B-A-rebuilt");event("A_rebuilt_B_rendered");
 // Failure is injected only after a fence-complete draw.
 try{a->render(masks[1],out/"A-before-failure");throw std::runtime_error("CONTROLLED_AFTER_COMPLETED_DRAW");}catch(const std::runtime_error& e){if(std::string(e.what())!="CONTROLLED_AFTER_COMPLETED_DRAW")throw;a.reset();}
 if(validationErrors)throw std::runtime_error("validation during failure cleanup");b->render(masks[1],out/"B-after-failure");event("A_failure_cleaned_B_rendered");
 b->render(masks[0],out/"B-wrong-input");event("legal_wrong_input_draw");
 if(masks!=saved)throw std::runtime_error("shared CPU input mutated");b.reset();}
 events<<"{\"phase\":\"all_destroyed\",\"live\":"<<Output::live<<",\"created\":"<<Output::created<<",\"destroyed\":"<<Output::destroyed<<"}\n";if(validationErrors||Output::live||Output::created!=Output::destroyed)throw std::runtime_error("final cleanup mismatch");std::cout<<"DUAL_DEVICE_PASS validation_enabled=1\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
