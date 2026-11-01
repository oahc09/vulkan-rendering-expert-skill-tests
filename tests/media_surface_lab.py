"""Executable isolated state model, NOT Android/Vulkan implementation or GPU evidence.

Reject invalid transitions; counters represent simulated events, never real fences.
No API handles, images, permissions, camera or hardware access are used.
"""
from dataclasses import dataclass, field


class ContractError(ValueError):
    pass


@dataclass
class Output:
    generation: int = 1
    active: bool = True
    accessing: bool = False
    capabilities: set = field(default_factory=lambda: {('rgba8', 'sdr', 'opaque')})


@dataclass
class Lease:
    frame_id: int
    generation: int
    timestamp: int
    acquire_ready: bool = False
    fd_owner: str = 'app'
    consumers: dict = field(default_factory=dict)
    released_to_foreign: bool = False
    returned: bool = False


class Lab:
    def __init__(self, max_images=4):
        if max_images < 1:
            raise ContractError('max_images must be positive')
        self.outputs = {'A': Output(), 'B': Output()}
        self.source_generation = 1
        self.device_lost = False
        self.max_images = max_images
        self.leases = {}
        self.next_id = 1
        self.peak_leases = 0
        self.returned = 0

    def acquire(self, timestamp, fd=-1):
        if self.device_lost or len(self.leases) >= self.max_images:
            raise ContractError('device unavailable or bounded backpressure')
        if fd < -1:
            raise ContractError('invalid sync FD')
        frame = Lease(self.next_id, self.source_generation, timestamp,
                      acquire_ready=(fd == -1), fd_owner='none' if fd == -1 else 'app')
        self.next_id += 1
        self.leases[frame.frame_id] = frame
        self.peak_leases = max(self.peak_leases, len(self.leases))
        return frame

    def live(self, frame):
        if self.leases.get(frame.frame_id) is not frame or frame.returned:
            raise ContractError('not a live lease')
        return frame

    def import_fd(self, frame, success):
        self.live(frame)
        if frame.fd_owner != 'app':
            raise ContractError('FD not application-owned')
        if success:
            frame.fd_owner = 'vulkan'
        # Failed import deliberately retains owner and unreadiness.

    def ready(self, frame):
        self.live(frame)
        if frame.fd_owner not in ('app', 'vulkan', 'none'):
            raise ContractError('readiness cannot follow closed unready FD')
        frame.acquire_ready = True

    def close_app_fd(self, frame):
        self.live(frame)
        if frame.fd_owner != 'app':
            raise ContractError('double close or transferred FD')
        if not frame.acquire_ready:
            raise ContractError('must preserve pending readiness dependency')
        frame.fd_owner = 'closed'

    def submit(self, frame, output, generation, success=True):
        self.live(frame)
        out = self.outputs[output]
        if (self.device_lost or not frame.acquire_ready or not out.active
                or generation != out.generation or frame.generation != self.source_generation
                or frame.released_to_foreign or output in frame.consumers):
            raise ContractError('not ready, stale or already handed off')
        if success:
            frame.consumers[output] = 'pending'
        # Failed submission adds no work; previous consumers remain pending.

    def complete(self, frame, output):
        self.live(frame)
        if self.device_lost or frame.consumers.get(output) != 'pending':
            raise ContractError('completion requires submitted live-device work')
        frame.consumers[output] = 'complete'

    def release_ownership(self, frame):
        self.live(frame)
        if not frame.acquire_ready or any(v != 'complete' for v in frame.consumers.values()):
            raise ContractError('all consumers must complete before modeled release')
        if self.device_lost:
            raise ContractError('lost device is not completion proof')
        frame.released_to_foreign = True

    def return_frame(self, frame, export_success=True):
        self.live(frame)
        if not export_success:
            return False  # Lease retained; fallback may wait existing completions.
        if not frame.released_to_foreign or frame.fd_owner == 'app':
            raise ContractError('missing ownership release or unhandled app FD')
        frame.returned = True
        del self.leases[frame.frame_id]
        self.returned += 1
        return True

    def destroy_output(self, output, generation, acknowledged):
        out = self.outputs[output]
        if generation != out.generation:
            return False
        if not acknowledged or out.accessing:
            raise ContractError('Surface access must stop before callback return')
        out.active = False
        return True

    def recreate_output(self, output):
        out = self.outputs[output]
        if out.active:
            raise ContractError('stop old Surface first')
        out.generation += 1
        out.active = True
        out.capabilities.clear()  # Must query actual new Surface, never inherit HDR.

    def change_source(self):
        if self.leases:
            raise ContractError('drain old-generation leases before reader replacement')
        self.source_generation += 1

    def update_capabilities(self, output, generation, capabilities):
        out = self.outputs[output]
        if generation != out.generation or not out.active:
            raise ContractError('stale or inactive Surface capability query')
        out.capabilities = set(capabilities)

    def choose_color(self, output, desired):
        capabilities = self.outputs[output].capabilities
        if desired in capabilities:
            return desired
        fallback = ('rgba8', 'sdr', 'opaque')
        if fallback not in capabilities:
            raise ContractError('no supported fallback: stop output')
        return fallback

    def hdr_metadata_allowed(self, output, extension, feature_enabled, surface_support):
        return bool(extension and feature_enabled and surface_support
                    and any(c[1] == 'hdr' for c in self.outputs[output].capabilities))

    def latest_can_discard(self):
        return self.max_images - len(self.leases) >= 2


def simulate(rebuilds=100, frames=1000):
    lab = Lab()
    for _ in range(rebuilds):
        old = lab.outputs['A'].generation
        lab.destroy_output('A', old, acknowledged=True)
        lab.recreate_output('A')
        lab.update_capabilities('A', lab.outputs['A'].generation, {('rgba8', 'sdr', 'opaque')})
        assert not lab.destroy_output('A', old, acknowledged=True)
        assert lab.outputs['B'].active
    for timestamp in range(frames):
        f = lab.acquire(timestamp, fd=0)
        lab.import_fd(f, success=True)
        lab.ready(f)
        for output in ('A', 'B'):
            lab.submit(f, output, lab.outputs[output].generation)
        lab.complete(f, 'A')
        try:
            lab.release_ownership(f)
        except ContractError:
            pass
        else:
            raise AssertionError('early release accepted')
        lab.complete(f, 'B')
        lab.release_ownership(f)
        assert lab.return_frame(f)
    return dict(layer='Static', implementation='isolated Python state fixture',
                gpu_executed=False, android_executed=False, rebuilds=rebuilds,
                dual_consumer_frames=frames, peak_leases=lab.peak_leases,
                outstanding_leases=len(lab.leases), returned=lab.returned,
                claims='State transition simulation only; no device/runtime/performance evidence')


if __name__ == '__main__':
    import json
    print(json.dumps(simulate(), indent=2))


def premultiply(rgb, alpha):
    """Linear-workspace CPU reference only, not transfer/gamut conversion."""
    if not 0 <= alpha <= 1:
        raise ContractError('alpha outside fixed fixture domain')
    return tuple(c * alpha for c in rgb)


def source_over(src_premult, src_alpha, dst_premult, dst_alpha):
    if not (0 <= src_alpha <= 1 and 0 <= dst_alpha <= 1):
        raise ContractError('alpha outside fixed fixture domain')
    return (tuple(s + d * (1-src_alpha) for s,d in zip(src_premult,dst_premult)),
            src_alpha + dst_alpha*(1-src_alpha))
