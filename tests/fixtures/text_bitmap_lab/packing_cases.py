"""Real glyph rectangles -> CPU shelf atlas -> Vulkan full-page upload/readback.
This verifies packed page bytes/composition, not a UV-quad glyph draw pipeline.
"""
import importlib.util,json,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def run_cases(build,out,font):
    sys.path.insert(0,str(ROOT/'tests'))
    try:from text_atlas_packing import ShelfAtlas
    finally:sys.path.pop(0)
    spec=importlib.util.spec_from_file_location('packing_bitmap',HERE/'run_lab.py');bitmap=importlib.util.module_from_spec(spec);spec.loader.exec_module(bitmap)
    rectangles=[];receipts=[]
    for letter in ('O','f','i'):
        mask,receipt=bitmap.raster(font,letter,'ltr','en')
        if len(receipt['glyphs'])!=1:raise ValueError('single glyph fixture')
        occupied=[(i%65,i//65) for i,v in enumerate(mask) if v]
        x0=min(x for x,y in occupied);x1=max(x for x,y in occupied)+1;y0=min(y for x,y in occupied);y1=max(y for x,y in occupied)+1
        rectangles.append((x1-x0,y1-y0,[mask[y*65+x] for y in range(y0,y1) for x in range(x0,x1)]));receipts.append(receipt)
    atlas=ShelfAtlas(24,24,max_pages=4,padding=1)
    places=list(atlas.publish(atlas.prepare(rectangles)));first=atlas.snapshot()
    if len(first)<2:raise ValueError('fixture did not exercise page growth')
    for i in range(len(first)):atlas.seal(i)
    canceled=atlas.prepare([rectangles[0]]);atlas.cancel(canceled)
    try:atlas.publish(canceled)
    except ValueError:pass
    else:raise ValueError('canceled staging published')
    if atlas.snapshot()!=first:raise ValueError('cancellation changed published bytes')
    places+=list(atlas.publish(atlas.prepare([rectangles[0]])));rectangles.append(rectangles[0])
    pages=atlas.snapshot()
    if pages[:len(first)]!=first:raise ValueError('sealed page rewritten')
    # Independent disjoint placement, zero padding and pixel reconstruction.
    expected=[[0.]*(24*24) for _ in pages];used=set()
    for n,p in enumerate(places):
        if p.x<1 or p.y<1 or p.x+p.width+1>24 or p.y+p.height+1>24:raise ValueError('padding boundary')
        for q in places[n+1:]:
            if p.page!=q.page:continue
            if not (p.x+p.width+1<=q.x-1 or q.x+q.width+1<=p.x-1 or p.y+p.height+1<=q.y-1 or q.y+q.height+1<=p.y-1):raise ValueError('padding overlap')
    for p,(w,h,pixels) in zip(places,rectangles):
        for y in range(h):
            for x in range(w):
                index=(p.y+y)*24+p.x+x;identity=(p.page,index)
                if identity in used:raise ValueError('overlapping glyph rectangles')
                used.add(identity);expected[p.page][index]=pixels[y*w+x]
    if tuple(tuple(p) for p in expected)!=pages:raise ValueError('atlas reconstruction/padding mismatch')
    rows=[]
    for n,page in enumerate(pages):
        folder=out/f'packed-page-{n}';folder.mkdir(exist_ok=False)
        mask=[page[y*24+x] if x<24 and y<24 else 0. for y in range(49) for x in range(65)]
        (folder/'mask.f32').write_bytes(struct.pack('<3185f',*mask))
        p=subprocess.run([str(build/'bitmap_lab'),str(build/'shaders'),str(folder/'mask.f32'),str(folder/'gpu')],capture_output=True,text=True,timeout=120)
        log=p.stdout+p.stderr;(folder/'vulkan.log').write_text(log)
        if p.returncode or 'VALIDATION:' in log or 'validation_enabled=1' not in log:raise RuntimeError('packed page GPU failure')
        row=bitmap.verify(folder);row.update(page=n,validation_enabled=True);rows.append(row)
    (out/'packing-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    return {'scope':'CPU padded shelf atlas of true glyph masks; whole packed pages sampled through Vulkan; not UV-glyph draws','input_glyph_rectangles':3,'published_rectangles':4,'initial_pages':len(first),'final_pages':len(pages),'page_extent':[24,24],'padding':1,'canceled_staging_preserved_published':True,'sealed_pages_unchanged':True,'cases':rows}
