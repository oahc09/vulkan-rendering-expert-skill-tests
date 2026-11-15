"""Local diagnostic only: CPU Reinhard+sRGB of actual HDR readback, not GPU output stage."""
import struct,sys,zlib,math
from pathlib import Path
raw=Path(sys.argv[1]).read_bytes()
if len(raw)!=65*49*16:raise ValueError('preview size')
f=struct.unpack('<12740f',raw)
if not all(math.isfinite(v) and v>=0 for v in f):raise ValueError('preview values')
def enc(v):
 v=v/(1+v);return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
data=b''.join(b'\0'+bytes(enc(f[(y*65+x)*4+c]) for x in range(65) for c in range(3)) for y in range(49))
def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v))
Path(sys.argv[2]).write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',65,49,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b''))
