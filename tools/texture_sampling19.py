"""Bounded normalized nearest RGBA8 sampler fixture, not generic sampling proof."""
import math
VUID='VUID-VkSamplerCreateInfo-unnormalizedCoordinates-01073'
def sampler(m):
 keys={'minFilter','magFilter','mipmapMode','addressU','addressV','addressW','minLod','maxLod','unnormalized','anisotropyEnable','compareEnable'}
 if not isinstance(m,dict) or set(m)!=keys:return {'status':'UNKNOWN','vuids':[]}
 if any(type(v) not in (int,float) or not math.isfinite(v) for v in m.values()):return {'status':'UNKNOWN','vuids':[]}
 if any(type(m[k]) is not int for k in keys-{'minLod','maxLod'}):return {'status':'UNKNOWN','vuids':[]}
 if any(m[k]!=0 for k in ('minFilter','magFilter','minLod','maxLod','anisotropyEnable','compareEnable')) or any(m[k]!=2 for k in ('addressU','addressV','addressW')):return {'status':'OUT_OF_SCOPE','vuids':[]}
 if m['unnormalized']==1 and m['mipmapMode']==1:return {'status':'REJECTED','vuids':[VUID]}
 if m['unnormalized']==0 and m['mipmapMode']==0:return {'status':'NEAREST_CLAMP_SCOPE','vuids':[]}
 return {'status':'OUT_OF_SCOPE','vuids':[]}
def reference():
 # Independent channel tuples and normalized-coordinate sampling arithmetic.
 texture=[(255 if x==0 else 0,255 if y<2 else 0,255 if x<1+y%3 else 0,255) for y in range(4) for x in range(4)]
 out=[]
 for y in range(4):
  for x in range(4):
   u=(x-.5)/4;v=(y+1.5)/4;sx=max(0,min(3,math.floor(u*4)));sy=max(0,min(3,math.floor(v*4)));out.append(sum(c<<(8*i) for i,c in enumerate(texture[sy*4+sx])))
 return out
