"""Bounded CPU shelf packer with transactional publication; not GPU allocator.
Fixed-size pages grow by count, never relocate existing rectangles. A sealed
page accepts no new data. This deterministic reference is not optimal packing.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Packed:
    page:int
    x:int
    y:int
    width:int
    height:int

@dataclass
class Batch:
    owner:object
    revision:int
    pages:list
    placements:tuple
    cancelled:bool=False

class ShelfAtlas:
    def __init__(self,width=24,height=24,*,max_pages=4,padding=1):
        if any(type(v)!=int for v in (width,height,max_pages,padding)) or not 1<=width<=256 or not 1<=height<=256 or not 1<=max_pages<=16 or not 1<=padding<=8:raise ValueError('atlas budget')
        self.width=width;self.height=height;self.max_pages=max_pages;self.padding=padding
        self.pages=[];self.revision=0;self._owner=object()

    def prepare(self,rectangles):
        if not isinstance(rectangles,(list,tuple)) or not 1<=len(rectangles)<=256:raise ValueError('batch budget')
        normalized=[]
        for w,h,data in rectangles:
            if type(w)!=int or type(h)!=int or min(w,h)<1 or w+2*self.padding>self.width or h+2*self.padding>self.height:raise ValueError('oversize rectangle')
            if len(data)!=w*h or any(not math.isfinite(v) or not 0<=v<=1 for v in data):raise ValueError('coverage data')
            normalized.append((w,h,tuple(data)))
        pages=[dict(p,pixels=list(p['pixels'])) for p in self.pages];placements=[]
        for w,h,data in normalized:
            rw,rh=w+2*self.padding,h+2*self.padding
            target=None
            for i,p in enumerate(pages):
                if p['sealed']:continue
                x,y,row=p['x'],p['y'],p['row']
                if x+rw>self.width:x,y,row=0,y+row,0
                if y+rh<=self.height:target=(i,x,y,row);break
            if target is None:
                if len(pages)>=self.max_pages:raise ValueError('page budget exceeded')
                pages.append(dict(x=0,y=0,row=0,sealed=False,pixels=[0.]*(self.width*self.height)))
                target=(len(pages)-1,0,0,0)
            i,x,y,row=target;p=pages[i];px=x+self.padding;py=y+self.padding
            for j in range(h):p['pixels'][(py+j)*self.width+px:(py+j)*self.width+px+w]=data[j*w:(j+1)*w]
            p.update(x=x+rw,y=y,row=max(row,rh));placements.append(Packed(i,px,py,w,h))
        return Batch(self._owner,self.revision,pages,tuple(placements))

    def publish(self,batch):
        if batch.owner is not self._owner or batch.cancelled or batch.revision!=self.revision:raise ValueError('stale/cancelled batch')
        # Copy ownership: future caller mutations of a staging batch cannot change
        # published bytes. Batch is an internal capability, not untrusted input.
        self.pages=[dict(p,pixels=list(p['pixels'])) for p in batch.pages]
        self.revision+=1;batch.cancelled=True
        return batch.placements

    def seal(self,page):
        if type(page)!=int or not 0<=page<len(self.pages):raise ValueError('page identity')
        self.pages[page]['sealed']=True;self.revision+=1

    def snapshot(self):return tuple(tuple(p['pixels']) for p in self.pages)

    @staticmethod
    def cancel(batch):batch.cancelled=True
