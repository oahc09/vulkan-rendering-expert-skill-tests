"""Original FP64 semantic oracles/policies. Not bit-exact GPU or mobile evidence."""
from dataclasses import dataclass
from math import exp, expm1, isfinite, pi
import struct


def finite(values):
    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and isfinite(x) for x in values):
        raise ValueError('Finite numeric input required')


def rgba(value):
    if len(value)!=4:raise ValueError('Expected RGBA')
    finite(value)
    if not 0<=value[3]<=1:raise ValueError('Opacity outside [0,1]')
    return tuple(value)


def source_over(src, dst, *, representation='premultiplied'):
    src,dst=rgba(src),rgba(dst)
    if representation not in {'straight','premultiplied'}:raise ValueError('Explicit alpha representation required')
    # Destination always premultiplied linear; source may be straight linear.
    rgb=src[:3] if representation=='premultiplied' else [c*src[3] for c in src[:3]]
    out=(*[rgb[i]+(1-src[3])*dst[i] for i in range(3)],src[3]+(1-src[3])*dst[3])
    finite(out);return out


def stored(value,fmt):
    finite(value)
    if fmt=='fp64':return tuple(value)
    if fmt=='rgba8':return tuple(round(min(1,max(0,x))*255)/255 for x in value)
    if fmt=='fp16':
        try:return tuple(struct.unpack('e',struct.pack('e',x))[0] for x in value)
        except OverflowError as exc:raise ValueError('FP16 range exceeded') from exc
    raise ValueError('Unknown storage format')


def accumulate(layers, *, fmt='fp64'):
    """Input ordered back-to-front, straight linear RGBA; quantize after each write."""
    out=(0.,0.,0.,0.)
    for layer in layers:out=stored(source_over(layer,out,representation='straight'),fmt)
    return out


def transmittance_front_to_back(layers):
    c=[0.,0.,0.];t=1.
    for item in layers:
        r,g,b,a=rgba(item)
        for i,v in enumerate((r,g,b)):c[i]+=t*a*v
        t*=1-a
    finite((*c,t));return (*c,1-t)


def wboit(layers):
    """Constant positive weight fixture; an approximate compositing operator."""
    accum=[0.,0.,0.];weight=0.;reveal=1.
    for item in layers:
        r,g,b,a=rgba(item)
        for i,v in enumerate((r,g,b)):accum[i]+=v*a
        weight+=a;reveal*=1-a
        finite((*accum,weight,reveal))
    return (*[(v/weight)*(1-reveal) if weight else 0. for v in accum],1-reveal)


def select_transparency_path(*,independent_blend,accum_blend,reveal_blend,multipass_allowed=False):
    if not (accum_blend and reveal_blend):return 'sorted'
    if independent_blend:return 'wboit_mrt'
    return 'wboit_multipass' if multipass_allowed else 'sorted'


def bounded_fragments(fragments,per_pixel_capacity,pool_remaining):
    for value in (per_pixel_capacity,pool_remaining):
        if type(value) is not int or value<0:raise ValueError('Invalid capacity')
    ids=[]
    for fragment in fragments:
        if not isinstance(fragment,dict) or set(fragment)!={'depth','id'}:raise ValueError('Explicit fragment record required')
        finite((fragment['depth'],))
        if type(fragment['id']) is not int or not 0<=fragment['id']<2**32:raise ValueError('Invalid stable ID')
        ids.append(fragment['id'])
    if len(set(ids))!=len(ids):raise ValueError('Duplicate stable ID')
    # Declared fixture policy is all-or-nothing refusal, never hidden truncation.
    overflow=max(0,len(fragments)-min(per_pixel_capacity,pool_remaining))
    return dict(status='overflow_rejected' if overflow else 'accepted',overflow=overflow,
                fragments=[] if overflow else sorted(fragments,key=lambda x:(-x['depth'],x['id'])))


def volume_transmittance(sigma,distance,step):
    finite((sigma,distance,step))
    if sigma<0 or distance<0 or step<=0:raise ValueError('Invalid world-unit extinction or step')
    ratio=distance/step
    if not isfinite(ratio) or ratio>100000:raise ValueError('Sampling safety budget exceeded')
    full=int(ratio)
    t=1.
    for _ in range(full):t*=exp(-sigma*step)
    return t*exp(-sigma*(distance-full*step))


def soft_particle(scene_distance,particle_distance,fade_distance):
    finite((scene_distance,particle_distance,fade_distance))
    if min(scene_distance,particle_distance)<0 or fade_distance<=0:raise ValueError('Positive linear distances required')
    return min(1.,max(0.,(scene_distance-particle_distance)/fade_distance))


@dataclass(frozen=True)
class GaussianProfile:
    scale: str
    opacity: str
    quaternion: str
    color: str


def decode_gaussian(position,scale,opacity,rotation,color,*,profile):
    if not isinstance(profile,GaussianProfile):raise ValueError('Explicit profile required')
    if profile not in (GaussianProfile('linear','probability','wxyz','linear_rgb'),GaussianProfile('log','logit','xyzw','sh_dc')):
        raise ValueError('Unknown profile; no field-name guesses')
    if len(position)!=3 or len(scale)!=3 or len(rotation)!=4 or len(color)!=3:raise ValueError('Invalid field count')
    finite((*position,*scale,opacity,*rotation,*color))
    try:s=tuple(exp(v) for v in scale) if profile.scale=='log' else tuple(scale)
    except OverflowError as exc:raise ValueError('Scale overflow') from exc
    if any(not isfinite(v) or v<=0 or v>1e6 for v in s):raise ValueError('Invalid positive bounded scale')
    # Stable sigmoid avoids overflow for large negative logits.
    a=(1/(1+exp(-opacity)) if opacity>=0 else exp(opacity)/(1+exp(opacity))) if profile.opacity=='logit' else opacity
    if not 0<=a<=1:raise ValueError('Invalid opacity')
    q=tuple(rotation) if profile.quaternion=='wxyz' else (rotation[3],*rotation[:3])
    # hypot-style scaling avoids overflow/underflow in quaternion normalization.
    m=max(abs(x) for x in q)
    if m==0:raise ValueError('Zero quaternion')
    q=tuple(x/m for x in q);n=sum(x*x for x in q)**.5;q=tuple(x/n for x in q)
    rgb=tuple(color) if profile.color=='linear_rgb' else tuple(.5+.28209479177387814*x for x in color)
    finite(rgb)
    return dict(position=tuple(position),scale=s,opacity=a,rotation=q,color=rgb)


def covariance_valid(c):
    if len(c)!=6:return False
    try:finite(c)
    except ValueError:return False
    xx,xy,xz,yy,yz,zz=c
    # Sylvester criterion for positive-definite symmetric covariance, with scale normalization.
    m=max(abs(x) for x in c)
    if m==0:return False
    xx,xy,xz,yy,yz,zz=(x/m for x in c)
    return xx>0 and xx*yy-xy*xy>0 and xx*(yy*zz-yz*yz)-xy*(xy*zz-yz*xz)+xz*(xy*yz-yy*xz)>0


def footprint_visible(cx,cy,rx,ry,*,width,height,z,near):
    finite((cx,cy,rx,ry,width,height,z,near))
    if rx<=0 or ry<=0 or width<=0 or height<=0 or near<=0:raise ValueError('Invalid footprint')
    if z<=near:return 'near_plane_fallback' # Defined bounded fallback, not claim of exact clipping.
    return 'visible' if cx+rx>=0 and cy+ry>=0 and cx-rx<width and cy-ry<height else 'culled'


@dataclass(frozen=True)
class SortKey:
    engine: int
    view: int
    camera: tuple
    transforms: tuple
    time: float
    parameters: str
    lod: tuple
    visible_ids: tuple
    generations: tuple
    index_policy: str


def sort_cache_valid(old,new):
    if not isinstance(new,SortKey) or not isinstance(old,SortKey):return False
    finite((*new.camera,new.time,*old.camera,old.time))
    return old==new


def coverage_estimate(radii,visible_count):
    if type(visible_count) is not int or visible_count!=len(radii):raise ValueError('Count mismatch')
    finite([x for r in radii for x in r])
    if any(len(r)!=2 or min(r)<=0 for r in radii):raise ValueError('Invalid radii')
    return dict(kind='unclipped_geometric_estimate_not_hardware_counter',count=visible_count,
                ellipse_area=sum(pi*rx*ry for rx,ry in radii),quad_area=sum(4*rx*ry for rx,ry in radii))
