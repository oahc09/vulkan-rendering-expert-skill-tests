#version 450
void main(){vec2 corners[6]=vec2[](vec2(0,0),vec2(1,0),vec2(0,1),vec2(0,1),vec2(1,0),vec2(1,1));int tile=gl_VertexIndex/6;vec2 pos=(vec2(tile%4,tile/4)+corners[gl_VertexIndex%6])/2.0-1.0;gl_Position=vec4(pos,0,1);}
