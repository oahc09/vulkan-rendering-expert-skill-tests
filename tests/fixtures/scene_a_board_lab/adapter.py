"""Frozen finite Scene A layout; real HB positions and unhinted FT raster/outline."""
import importlib.util,json,hashlib,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent; W=65;H=49

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def outline(slot):
 contours=[];current=[];point=start=None
 def xy(p):return (6+p.x/64,32-p.y/64)
 def close():
  nonlocal current
  if current:
   if point!=start:current.append([point,start])
   contours.append(current)
  current=[]
 def move(p,_):
  nonlocal point,start
  close();point=start=xy(p)
 def line(p,_):
  nonlocal point
  q=xy(p);current.append([point,q]);point=q
 def conic(c,p,_):
  nonlocal point
  q=xy(p);current.append([point,xy(c),q]);point=q
 def cubic(c,d,p,_):
  nonlocal point
  q=xy(p);current.append([point,xy(c),xy(d),q]);point=q
 slot.outline.decompose(move_to=move,line_to=line,conic_to=conic,cubic_to=cubic);close();return contours

def prepare(variable_font):
 import freetype as ft
 a=load(HERE.parent/'text_fallback_lab/adapter.py','board_fallback')
 old=load(HERE.parent/'text_fallback_lab/run_lab.py','board_fallback_run')
 va=load(HERE.parent/'text_variation_churn_lab/adapter.py','board_variation')
 bidi=load(HERE.parent/'text_bidi_lab/bidi.py','board_bidi')
 specs=[('chinese','中文',18,'zh',None),('ligature','ffi',20,'en',None),('combining','a\u0301',20,'en',None),('bidi',bidi.TEXT,10,'en',None),('variable-light','Ofi',18,'en',{'wght':100,'wdth':75}),('variable-heavy','Ofi',18,'en',{'wght':900,'wdth':125})]
 golden=json.loads((HERE.parent/'text_fallback_lab/expected-shaping.json').read_text())['runs']
 rows=[]
 for name,text,px,lang,axes in specs:
  bidi_mapping=None
  if name=='bidi':runs,bidi_mapping=bidi.runs(text,0)
  else:runs=[dict(text=text,direction='ltr',language=lang)]
  layers=[];receipts=[];cursor=0.
  for run in runs:
   if axes is None:
    key,receipt,attempts=old.fallback(a,run['text'],run['direction'],run['language']);path=old.FONTS[key];index=a.guard(path,key)
   else:
    path=Path(variable_font);receipt=va.shape(path,run['text'],direction=run['direction'],language=run['language'],variation_axes=axes);index=0;key='variable'
   if run['text'] in golden:
    expected=golden[run['text']]
    for field,value in expected.items():
     if receipt.get(field)!=value:raise ValueError('prior shaping regression mismatch '+field)
   if any(g['y_advance']!=0 for g in receipt['glyphs']):raise ValueError('vertical advance unsupported')
   if receipt['missing_glyphs']:raise ValueError('missing glyph in frozen row')
   face=ft.Face(str(path),index=index);face.set_pixel_sizes(0,px)
   if axes is not None:
    axisinfo,values=va.coordinates(face,axes);face.set_var_design_coords(values)
    if list(face.get_var_design_coords())!=receipt['ft_design_coordinates']:raise ValueError('axis mismatch')
   runstart=cursor
   for g in receipt['glyphs']:
    dx=round((cursor+g['x_offset']*px/receipt['upem'])*64);dy=round(g['y_offset']*px/receipt['upem']*64)
    face.set_transform(ft.Matrix(65536,0,0,65536),ft.Vector(dx,dy))
    face.load_glyph(g['id'],ft.FT_LOAD_NO_HINTING|ft.FT_LOAD_NO_BITMAP)
    contours=outline(face.glyph)
    face.glyph.render(ft.FT_RENDER_MODE_NORMAL);b=face.glyph.bitmap
    if b.rows and (b.pixel_mode!=ft.FT_PIXEL_MODE_GRAY or b.num_grays!=256 or b.pitch<b.width or b.pitch<=0):raise ValueError('gray bitmap format')
    if not contours and any(b.buffer):raise ValueError('bitmap-only glyph requires explicit fallback')
    left=6+face.glyph.bitmap_left;top=32-face.glyph.bitmap_top
    data=[0.]*(W*H)
    for y in range(b.rows):
     for x in range(b.width):
      value=b.buffer[y*b.pitch+x]/255
      if value and not(0<=left+x<W and 0<=top+y<H):raise ValueError('frozen bitmap clipped '+name)
      if 0<=left+x<W and 0<=top+y<H:data[(top+y)*W+left+x]=value
    if contours:
     layers.append(dict(glyph_id=g['id'],font_sha256=receipt['font_sha256'],face_index=index,origin_26_6=[dx,dy],outline=contours,bitmap=data,bitmap_bounds=[left,top,left+b.width,top+b.rows]))
    cursor+=g['x_advance']*px/receipt['upem']
   receipts.append(dict(bidi_run=run,text=run['text'],cursor_start=runstart,cursor_end=cursor,shape=receipt))
  if not 0<len(layers)<=16:raise ValueError('layer budget')
  rows.append(dict(name=name,text=text,ppem=px,receipts=receipts,bidi_mapping=bidi_mapping,layers=layers,advance=cursor))
 return rows
