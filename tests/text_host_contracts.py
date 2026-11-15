"""TEXT18 CPU reference contracts. Not production font, Vulkan or platform code."""
from dataclasses import dataclass
import math


def uint(value, maximum=2**32-1):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError('integer range')
    return value


def canonical_option(value):
    if type(value) in (str, int, bool, type(None)): return
    if type(value) is float and math.isfinite(value): return
    if type(value) is tuple:
        for item in value: canonical_option(item)
        return
    raise ValueError('generation option must be finite immutable data')


@dataclass(frozen=True)
class GlyphKey:
    provider: str
    face: str
    face_generation: int
    glyph: int
    variation: tuple
    representation: str
    pixel_size: int
    synthetic_style: str = ''
    palette: int = 0
    subpixel_phase: tuple = (0.0, 0.0)
    distance_range: float = 0.0
    render_mode: str = 'default'
    generation_options: tuple = ()

    def __post_init__(self):
        if not self.provider or not self.face or self.representation not in ('coverage','color','msdf','mtsdf','mesh'):
            raise ValueError('identity/representation')
        uint(self.face_generation); uint(self.glyph); uint(self.pixel_size); uint(self.palette)
        if (not isinstance(self.synthetic_style, str) or not isinstance(self.render_mode, str)
                or not self.render_mode or not isinstance(self.subpixel_phase, tuple)
                or len(self.subpixel_phase) != 2
                or any(not math.isfinite(v) for v in self.subpixel_phase)
                or not math.isfinite(self.distance_range) or self.distance_range < 0
                or not isinstance(self.generation_options, tuple)):
            raise ValueError('render identity/options')
        canonical_option(self.generation_options)
        if self.pixel_size == 0 or not isinstance(self.variation, tuple):
            raise ValueError('size/variation')
        axes = [a for a, v in self.variation]
        if axes != sorted(set(axes)) or any(not math.isfinite(v) for a,v in self.variation):
            raise ValueError('axes must be finite, unique and canonical')


def provider_glyph(glyph, bits):
    if bits not in (16, 24, 32):
        raise ValueError('unknown provider range')
    return uint(glyph, 2**bits-1)


class AtlasSlot:
    """One device-owned slot; consumer timelines are separate and monotonic.

    Snapshot references must be released AND all submitted consumers complete.
    Upload completion is not publication; stale face work never becomes visible.
    """
    def __init__(self, device, generation=0):
        self.device=device; self.generation=uint(generation)
        self.key=None; self.upload=None; self.published=False
        self.consumers={}; self.snapshots=0

    def prepare(self, key, device, upload_value, completed):
        if device != self.device or not self.reusable(completed):
            raise ValueError('device mismatch or slot still in use')
        if not isinstance(key, GlyphKey): raise ValueError('invalid glyph key')
        next_generation=uint(self.generation+1)
        next_upload=uint(upload_value)
        # Validate everything before mutation, including failed uploads/wraparound.
        self.generation=next_generation; self.key=key; self.upload=next_upload
        self.published=False; self.consumers={}; self.snapshots=0
        return self.generation

    def publish(self, generation, current_face_generation, upload_completed):
        uint(upload_completed)
        if (generation != self.generation or self.key is None or
            self.key.face_generation != current_face_generation or upload_completed < self.upload):
            return False
        self.published=True
        return True

    def retain(self, generation):
        if not self.published or generation != self.generation:
            raise ValueError('stale/unpublished snapshot')
        self.snapshots += 1

    def release(self):
        if self.snapshots == 0: raise ValueError('snapshot underflow')
        self.snapshots -= 1

    def submit(self, generation, device, queue, value):
        if not self.published or generation != self.generation or device != self.device or self.snapshots == 0:
            raise ValueError('invalid consumer')
        uint(value)
        self.consumers[queue]=max(value,self.consumers.get(queue,0))

    def reusable(self, completed):
        if self.key is None: return True
        for v in completed.values(): uint(v)
        return (self.snapshots == 0 and completed.get('upload',-1) >= self.upload and
                all(completed.get(q,-1) >= v for q,v in self.consumers.items()))


def linear_over(coverage, opacity, rgb, dst):
    values=(coverage,opacity,rgb,dst)
    if any(not math.isfinite(v) for v in values) or not 0 <= coverage <= 1 or not 0 <= opacity <= 1:
        raise ValueError('invalid linear color/coverage')
    a=coverage*opacity
    return rgb*a+dst*(1-a)


def checked_budget(*, segments, depth, vertices, bytes_used, max_segments=4096, max_depth=16, max_vertices=65536, max_bytes=2**20):
    values=(segments,depth,vertices,bytes_used)
    limits=(max_segments,max_depth,max_vertices,max_bytes)
    for v in values+limits: uint(v,2**63-1)
    return all(v <= limit for v,limit in zip(values,limits))
