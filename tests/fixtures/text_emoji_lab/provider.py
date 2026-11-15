"""Fixed trusted real emoji, explicit system FreeType library/handles."""
import ctypes as C,hashlib
from pathlib import Path
FONT=Path('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf')
SHA='dac5c27651082d6c53dab5081f50d2022ddf6877d730fa919cf6a4fc2af22de0'
def guard():
 if FONT.stat().st_size!=11260748 or hashlib.sha256(FONT.read_bytes()).hexdigest()!=SHA:raise ValueError('trusted emoji font mismatch')
def policy(text):
 if text=='❤\ufe0e':return 'text'
 if text=='❤\ufe0f':return 'emoji'
 raise ValueError('unsupported presentation cluster')
def decode(glyph_id):
 if glyph_id!=168:raise ValueError('unsupported emoji glyph identity')
 guard()
 from freetype.ft_structs import FT_Face,FT_Library
 h=C.CDLL('/lib/x86_64-linux-gnu/libfreetype.so.6')
 specs={'FT_Init_FreeType':[C.POINTER(FT_Library)],'FT_New_Face':[FT_Library,C.c_char_p,C.c_long,C.POINTER(FT_Face)],'FT_Select_Size':[FT_Face,C.c_int],'FT_Load_Glyph':[FT_Face,C.c_uint,C.c_int32],'FT_Done_Face':[FT_Face],'FT_Done_FreeType':[FT_Library]}
 for n,args in specs.items():getattr(h,n).argtypes=args;getattr(h,n).restype=C.c_int
 library=FT_Library();face=FT_Face()
 def ok(code):
  if code:raise ValueError('system FreeType error '+str(code))
 ok(h.FT_Init_FreeType(C.byref(library)))
 try:
  ok(h.FT_New_Face(library,str(FONT).encode(),0,C.byref(face)))
  try:
   ok(h.FT_Select_Size(face,0));ok(h.FT_Load_Glyph(face,glyph_id,(1<<20)|4));b=face.contents.glyph.contents.bitmap
   if (b.width,b.rows,b.pitch,b.pixel_mode)!=(136,128,544,7):raise ValueError('fixed BGRA strike format')
   data=C.string_at(b.buffer,b.pitch*b.rows)
  finally:ok(h.FT_Done_Face(face))
 finally:ok(h.FT_Done_FreeType(library))
 return data

def linear_pixel(bgra,decode_srgb=True):
 b,g,r,a=bgra
 if not a:return [0.,0.,0.,0.]
 if max(b,g,r)>a:raise ValueError('invalid premultiplied BGRA')
 rgb=[c/a for c in (r,g,b)]
 if decode_srgb:rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
 return [c*(a/255) for c in rgb]+[a/255]
