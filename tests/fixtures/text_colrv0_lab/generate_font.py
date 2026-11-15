"""Synthetic two-layer COLRv0 font; requires existing fontTools only for generation."""
import sys
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.colorLib.builder import buildCOLR,buildCPAL
fb=FontBuilder(1000,isTTF=True);order=['.notdef','base','back','front'];fb.setupGlyphOrder(order);fb.setupCharacterMap({0x41:'base'})
def rect(coords=None):
 p=TTGlyphPen(None)
 if coords:
  x0,y0,x1,y1=coords;p.moveTo((x0,y0));p.lineTo((x1,y0));p.lineTo((x1,y1));p.lineTo((x0,y1));p.closePath()
 return p.glyph()
fb.setupGlyf({'.notdef':rect(),'base':rect(),'back':rect((0,0,600,600)),'front':rect((300,300,900,900))});fb.setupHorizontalMetrics({n:(1000,300 if n=='front' else 0) for n in order});fb.setupHorizontalHeader(ascent=1000,descent=0);fb.setupNameTable({'familyName':'Synthetic TEXT18 COLRv0','styleName':'Regular','uniqueFontIdentifier':'TEXT18SyntheticCOLR','fullName':'Synthetic TEXT18 COLRv0','psName':'TEXT18SyntheticCOLR'});fb.setupOS2(sTypoAscender=1000,sTypoDescender=0,usWinAscent=1000,usWinDescent=0);fb.setupPost();fb.setupMaxp()
fb.font['COLR']=buildCOLR({'base':[('back',0),('front',1)]},version=0,glyphMap=fb.font.getReverseGlyphMap())
fb.font['CPAL']=buildCPAL([[(1.,0.,0.,128/255),(0.,0.,1.,192/255)],[(0.,1.,0.,192/255),(1.,1.,0.,128/255)],[(51/255,102/255,153/255,128/255),(204/255,51/255,102/255,192/255)]])
fb.font['head'].created=fb.font['head'].modified=2082844800;fb.font.recalcTimestamp=False;fb.save(sys.argv[1])
