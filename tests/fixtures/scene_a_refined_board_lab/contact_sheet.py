"""Post-readback presentation only. No generated image feeds the tested GPU path."""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
out=Path(sys.argv[1]);manifest=json.loads((out/'frozen-input-manifest.json').read_text());transforms=['native','minified','rotate90','phase-quarter','phase-half','square-rotate90']
w=1100;h=90+len(manifest)*110;im=Image.new('RGB',(w,h),(25,28,33));d=ImageDraw.Draw(im)
d.text((12,8),'Real multilingual Scene A: FT bitmap | MSDF linear4 (emoji: bitmap-only)',fill='white')
d.text((12,26),'Same frozen layout per row. Sampling checks != visual qualification. No perspective.',fill='white')
for j,t in enumerate(transforms):d.text((190+j*150,52),t,fill='white')
for i,row in enumerate(manifest):
 y=85+i*110;d.text((10,y),row['name'],fill='white');d.text((10,y+18),'ppem '+str(row['ppem']),fill='white')
 for j,t in enumerate(transforms):
  for mode in (0,1):
   x=190+j*150+mode*70;p=out/'gpu'/(row['name']+'-'+t+'-'+str(mode))/'preview.png'
   if p.exists():im.paste(Image.open(p),(x,y))
   else:d.text((x,y+18),'N/A',fill=(190,190,190))
  d.text((190+j*150,y+72),'bitmap | MSDF',fill=(180,180,180))
im.save(out/'board.png')
