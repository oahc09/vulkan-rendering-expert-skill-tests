"""Independent CBDT extraction and PNG decoder; invoked with system Python."""
import hashlib,json,sys,io
from pathlib import Path
from fontTools.ttLib import TTFont
from PIL import Image
p=Path(sys.argv[1]);out=Path(sys.argv[2])
if p.stat().st_size!=11260748 or hashlib.sha256(p.read_bytes()).hexdigest()!='dac5c27651082d6c53dab5081f50d2022ddf6877d730fa919cf6a4fc2af22de0':raise ValueError('trusted font')
f=TTFont(p);name=f.getGlyphName(168);glyph=f['CBDT'].strikeData[0][name];glyph.ensureDecompiled();im=Image.open(io.BytesIO(glyph.imageData)).convert('RGBA')
if im.size!=(136,128) or name!='uni2764':raise ValueError('CBDT identity/dimensions')
out.write_bytes(im.tobytes());print(json.dumps({'glyph_name':name,'size':im.size,'png_sha256':hashlib.sha256(glyph.imageData).hexdigest()}))
