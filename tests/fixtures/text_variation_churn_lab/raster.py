import adapter,hashlib
from pathlib import Path
WIDTH,HEIGHT=65,49
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raster(font,text,direction,language,*,pixel_size=20,phase64=0,variation_axes=None,_raster_axes_override=None):
    import freetype
    if type(pixel_size)!=int or not 1<=pixel_size<=28 or type(phase64)!=int or not 0<=phase64<64:raise ValueError('raster size/phase budget')
    provider=adapter
    run=provider.shape(font,text,direction=direction,language=language,variation_axes=variation_axes)
    if run['missing_glyphs'] or not 0<len(run['glyphs'])<=16:raise ValueError('unsupported glyph run')
    face=freetype.Face(str(font));axes,values=adapter.coordinates(face,({} if variation_axes is None else variation_axes) if _raster_axes_override is None else _raster_axes_override);face.set_var_design_coords(values)
    if list(face.get_var_design_coords())!=run["hb_design_coordinates"]:raise ValueError("raster axis mismatch")
    face.set_pixel_sizes(0,pixel_size)
    face.set_transform(freetype.Matrix(65536,0,0,65536),freetype.Vector(phase64,0))
    penx=4.;peny=32.;scale=pixel_size/run['upem'];mask=[0.]*(WIDTH*HEIGHT);placements=[];clipped=0
    for g in run['glyphs']:
        # True shaped glyph IDs, never codepoint substitution. Integer placement
        # deliberately defines this bitmap path; no fractional hinting claim.
        face.load_glyph(g['id'],freetype.FT_LOAD_RENDER|freetype.FT_LOAD_TARGET_NORMAL)
        slot=face.glyph;b=slot.bitmap
        if b.pixel_mode!=freetype.FT_PIXEL_MODE_GRAY or b.num_grays!=256 or b.pitch<0:raise ValueError('unsupported bitmap format')
        x=round(penx+g['x_offset']*scale)+slot.bitmap_left
        y=round(peny-g['y_offset']*scale)-slot.bitmap_top
        data=b.buffer
        for row in range(b.rows):
            for col in range(b.width):
                coverage=data[row*b.pitch+col]/255
                if not coverage:continue
                xx,yy=x+col,y+row
                if not (0<=xx<WIDTH and 0<=yy<HEIGHT):clipped+=1;continue
                i=yy*WIDTH+xx;mask[i]=coverage+mask[i]*(1-coverage)
        placements.append({'glyph_id':g['id'],'x':x,'y':y,'bitmap_width':b.width,'bitmap_rows':b.rows})
        penx+=g['x_advance']*scale;peny-=g['y_advance']*scale
    if clipped or not any(mask):raise ValueError('fixture clipped or blank')
    if text=='ffi' and len(run['glyphs'])>=3:raise ValueError('fixture requires real ligature')
    if direction=='rtl' and [g['cluster_utf8_byte'] for g in run['glyphs']]!=sorted((g['cluster_utf8_byte'] for g in run['glyphs']),reverse=True):raise ValueError('RTL cluster order')
    run.update(placements=placements,raster_provider='freetype-py',freetype_version=list(freetype.version()),freetype_library_sha256=sha(Path(freetype.raw._lib._name)),pixel_size=pixel_size,phase64=phase64,position_policy='round shaped positions to integer pixels; FT normal grayscale',clipped_samples=clipped)
    return mask,run
