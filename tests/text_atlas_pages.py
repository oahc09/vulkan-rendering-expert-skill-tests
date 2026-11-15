"""Externally serialized CPU page-routing reference; no GPU allocation proof.
Allocation/disposal callbacks are atomic on failure; partial backend effects remain the
backend's cleanup responsibility. Byte budgets describe R8 payload, not VRAM.
"""
from dataclasses import dataclass
from text_host_contracts import AtlasSlot, GlyphKey, uint

@dataclass
class Page:
    identity:int
    slot:AtlasSlot
    extent:tuple
    handle:object

class AtlasPages:
    def __init__(self,device,allocate,dispose,*,max_pages=2,max_payload_bytes=8192):
        if type(max_pages)!=int or not 1<=max_pages<=16:raise ValueError('page budget')
        uint(max_payload_bytes,2**32-1)
        if not max_payload_bytes:raise ValueError('payload budget')
        self.device=device;self.allocate=allocate;self.dispose=dispose
        self.max_pages=max_pages;self.max_payload_bytes=max_payload_bytes
        self.pages={};self.current=None;self.next_identity=1
        self.reserved_upload=0;self.consumer_signals={};self.published_identity=0

    @property
    def payload_bytes(self):return sum(p.extent[0]*p.extent[1] for p in self.pages.values())

    def prepare(self,key,extent,upload_value,completed):
        if not isinstance(key,GlyphKey) or not isinstance(extent,tuple) or len(extent)!=2:raise ValueError('page input')
        for v in extent:
            if type(v)!=int or not 1<=v<=4096:raise ValueError('extent')
        if len(self.pages)>=self.max_pages or self.payload_bytes+extent[0]*extent[1]>self.max_payload_bytes:raise ValueError('capacity')
        uint(upload_value,2**64-1)
        if upload_value<=self.reserved_upload:raise ValueError('upload value already reserved')
        identity=self.next_identity;uint(identity)
        slot=AtlasSlot(self.device);slot.prepare(key,self.device,upload_value,completed)
        # All local validations precede an atomic external allocator call.
        handle=self.allocate(extent)
        if handle is None:raise ValueError('allocator returned no resource')
        self.pages[identity]=Page(identity,slot,extent,handle)
        self.next_identity=identity+1;self.reserved_upload=upload_value
        return identity,slot.generation

    def publish(self,identity,generation,face_generation,upload_completed):
        page=self.pages.get(identity)
        if page is None or identity<self.published_identity:return False
        if not page.slot.publish(generation,face_generation,upload_completed):return False
        self.current=(identity,generation);self.published_identity=identity;return True

    def capture(self):
        if self.current is None:raise ValueError('no published page')
        identity,generation=self.current;self.pages[identity].slot.retain(generation)
        return self.current

    def cancel(self,identity,generation):
        page=self.pages.get(identity)
        if page is None:return False
        if not page.slot.cancel(generation):return False
        if self.current==(identity,generation):self.current=None
        return True

    def submit(self,snapshot,device,queue,value):
        identity,generation=snapshot
        if identity not in self.pages:raise ValueError('retired page')
        uint(value,2**64-1)
        if isinstance(queue,str) and value<self.consumer_signals.get(queue,0):raise ValueError('global consumer signal regression')
        self.pages[identity].slot.submit(generation,device,queue,value)
        self.consumer_signals[queue]=value

    def release(self,snapshot):
        identity,generation=snapshot
        p=self.pages.get(identity)
        if p is None or p.slot.generation!=generation:raise ValueError('stale snapshot')
        p.slot.release()

    def collect(self,completed):
        # Caller supplies verified device timeline observations. Never destroy
        # current routing or upload/consumer/snapshot-pending resources.
        AtlasSlot._completion_values(completed)
        retired=[]
        for identity,p in list(self.pages.items()):
            if self.current==(identity,p.slot.generation):continue
            if not p.slot.cancelled and not p.slot.published:continue  # pending publication still owns candidate
            if p.slot.reusable(completed):
                self.dispose(p.handle)  # on exception retain ownership for retry
                del self.pages[identity];retired.append(identity)
        return retired
