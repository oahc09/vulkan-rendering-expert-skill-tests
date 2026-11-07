#version 450
layout(push_constant) uniform Push { uint n,capacity,mode,flags,width,height,level,tick;float viewX,zoom;uint base,unused; } p;
layout(location=0) out vec2 uv;
layout(location=1) flat out uint material;
void main(){
 vec2 q[6]=vec2[](vec2(-1,-1),vec2(1,-1),vec2(1,1),vec2(-1,-1),vec2(1,1),vec2(-1,1));
 uv=q[gl_VertexIndex]*.5+.5; material=uint(gl_InstanceIndex);
 // Three original courtyard blockers: contact slab, animated cutout fence,
 // and caster outside camera x [-.65,.65], still in light frustum [-1,1].
 vec2 center=material==0u?vec2(-.25,0):material==1u?vec2(.2+.12*sin(float(p.tick)*.3),.15):vec2(.82,-.25);
 vec2 extent=material==0u?vec2(.18,.25):material==1u?vec2(.22,.4):vec2(.12,.2);
 float z=material==0u?.6:material==1u?.35:.2;
 float lightShear=p.zoom;
 vec2 lightXY=center+q[gl_VertexIndex]*extent+vec2(lightShear*(.8-z),0);
 gl_Position=vec4(lightXY,z,1);
}
