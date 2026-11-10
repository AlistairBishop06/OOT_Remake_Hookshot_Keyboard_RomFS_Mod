#!/usr/bin/env python3
"""SPDX-License-Identifier: GPL-3.0-or-later

Generate a genuine Hookshot RomFS keyboard prompt mod from the player's own game.

Hookshot loads a replacement Font2/Scalable/External font and the game's Common UI
texture atlas from RomFS mods. The font and texture atlas are generated from the
player's RomFS and current Hookshot keyboard bindings, not redistributed.

Works at game startup, not on-the-fly: the game caches the font and atlas.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import io
import os
from pathlib import Path
import struct
import sys
import tempfile
import zlib

FONT = Path('Font2/Scalable/External.Nin_Ounce_NVN2.bfotf.zs')
TEX = Path('UI/Layout2Archive/Common.Product.100.Nin_Ounce_NVN2.bntx.zs')
RESOURCE_DIR = Path('System/Resource')
MAGIC = 0x18029A7F
BUTTONS = ('a', 'b', 'x', 'y', 'ls', 'rs', 'l', 'r', 'zl', 'zr', 'plus', 'minus', 'left', 'up', 'right', 'down')
# Correct order and codepoints taken from Hookshot nx2/prompt_assets.py.
CODES = (0xE040, 0xE041, 0xE042, 0xE043, 0xE056, 0xE057, 0xE044, 0xE045,
         0xE046, 0xE047, 0xE04B, 0xE04C, 0xE062, 0xE060, 0xE063, 0xE061)
DEFAULTS = ((69, 0), (16, 0), (32, 0), (1, 0), (17, 0), (67, 0), (81, 0),
            (82, 0), (90, 2), (88, 70), (9, 13), (77, 0), (49, 0), (50, 0),
            (51, 0), (52, 0))
NOTE_TEXTURES = dict(OcarinaButtonA_00='a', OcarinaButtonB_00='b', OcarinaButtonX_00='x',
                     OcarinaButtonY_00='y', OcarinaButtonL_00='l', OcarinaButtonR_00='r')
LETTER_TEXTURES = dict(KeyTexFontA_00='a', KeyTexFontB_00='b', KeyTexFontX_00='x', KeyTexFontY_00='y')

# A tiny, self-contained 5x7 pixel alphabet, used for both vector (font) and bitmap (texture)
# keycaps. Font files from the player's system or the game are never packaged or shared.
GLYPHS = {
' ':('00000',)*7,
'A':('01110','10001','10001','11111','10001','10001','10001'),
'B':('11110','10001','10001','11110','10001','10001','11110'),
'C':('01111','10000','10000','10000','10000','10000','01111'),
'D':('11110','10001','10001','10001','10001','10001','11110'),
'E':('11111','10000','10000','11110','10000','10000','11111'),
'F':('11111','10000','10000','11110','10000','10000','10000'),
'G':('01111','10000','10000','10111','10001','10001','01111'),
'H':('10001','10001','10001','11111','10001','10001','10001'),
'I':('11111','00100','00100','00100','00100','00100','11111'),
'J':('00111','00010','00010','00010','10010','10010','01100'),
'K':('10001','10010','10100','11000','10100','10010','10001'),
'L':('10000','10000','10000','10000','10000','10000','11111'),
'M':('10001','11011','10101','10101','10001','10001','10001'),
'N':('10001','11001','10101','10011','10001','10001','10001'),
'O':('01110','10001','10001','10001','10001','10001','01110'),
'P':('11110','10001','10001','11110','10000','10000','10000'),
'Q':('01110','10001','10001','10001','10101','10010','01101'),
'R':('11110','10001','10001','11110','10100','10010','10001'),
'S':('01111','10000','10000','01110','00001','00001','11110'),
'T':('11111','00100','00100','00100','00100','00100','00100'),
'U':('10001','10001','10001','10001','10001','10001','01110'),
'V':('10001','10001','10001','10001','10001','01010','00100'),
'W':('10001','10001','10001','10101','10101','10101','01010'),
'X':('10001','10001','01010','00100','01010','10001','10001'),
'Y':('10001','10001','01010','00100','00100','00100','00100'),
'Z':('11111','00001','00010','00100','01000','10000','11111'),
'0':('01110','10011','10101','10101','11001','10001','01110'),
'1':('00100','01100','00100','00100','00100','00100','01110'),
'2':('01110','10001','00001','00010','00100','01000','11111'),
'3':('11110','00001','00001','01110','00001','00001','11110'),
'4':('00010','00110','01010','10010','11111','00010','00010'),
'5':('11111','10000','10000','11110','00001','00001','11110'),
'6':('01111','10000','10000','11110','10001','10001','01110'),
'7':('11111','00001','00010','00100','01000','01000','01000'),
'8':('01110','10001','10001','01110','10001','10001','01110'),
'9':('01110','10001','10001','01111','00001','00001','11110'),
'/':('00001','00001','00010','00100','01000','10000','10000'),
'-':('00000','00000','00000','11111','00000','00000','00000'),
'+':('00000','00100','00100','11111','00100','00100','00000'),
'.':('00000','00000','00000','00000','00000','01100','01100'),
':':('00000','01100','01100','00000','01100','01100','00000'),
'[':('01110','01000','01000','01000','01000','01000','01110'),
']':('01110','00010','00010','00010','00010','00010','01110'),
'?':('01110','10001','00001','00010','00100','00000','00100'),
}

VK = {1:'LMB',2:'RMB',4:'MMB',5:'M4',6:'M5',8:'BACK',9:'TAB',13:'ENTER',16:'SHIFT',
      17:'CTRL',18:'ALT',19:'PAUSE',20:'CAPS',27:'ESC',32:'SPACE',33:'PGUP',34:'PGDN',
      35:'END',36:'HOME',37:'LEFT',38:'UP',39:'RIGHT',40:'DOWN',45:'INS',46:'DEL',
      91:'WIN',92:'WIN',93:'MENU',106:'NUM*',107:'NUM+',109:'NUM-',110:'NUM.',111:'NUM/',
      144:'NUM',145:'SCRL',160:'LSHFT',161:'RSHFT',162:'LCTRL',163:'RCTRL',164:'LALT',165:'RALT',
      186:';',187:'=',188:',',189:'-',190:'.',191:'/',192:'`',219:'[',220:'\\',221:']',222:"'"}
for n in range(10):
    VK[0x60+n] = f'NUM{n}'
for n in range(1,25):
    VK[0x6F+n] = f'F{n}'


def label_for_vk(n: int) -> str:
    if n == 0:
        return ''
    if n in VK:
        return VK[n]
    if 48 <= n <= 57 or 65 <= n <= 90:
        return chr(n)
    return f'VK{n}'


def keyboard_bindings(path: Path, both: bool):
    cfg = dict(zip(BUTTONS, DEFAULTS))
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig', errors='replace').splitlines():
            key, sep, value = line.strip().partition('=')
            if sep and key.startswith('key_') and key[4:] in cfg:
                try:
                    xs = [int(v.strip()) for v in value.split(',')[:2]]
                    cfg[key[4:]] = (xs[0], xs[1] if len(xs) > 1 else 0)
                except ValueError:
                    print(f'  Warning: bad binding {line!r}; using previous value')
    out = {}
    for name, slots in cfg.items():
        labels = [label_for_vk(v) for v in slots if 0 < v < 256]
        labels = list(dict.fromkeys(labels))
        out[name] = '/'.join(labels) if both and labels else (labels[0] if labels else '-')
    return out


def draw_pixels(draw, label: str, x: float, y: float, pixel: float, fill):
    for k, char in enumerate(label.upper()):
        glyph = GLYPHS.get(char, GLYPHS['?'])
        for row, line in enumerate(glyph):
            for col, v in enumerate(line):
                if v == '1':
                    xx = x + (6*k + col)*pixel
                    yy = y + row*pixel
                    draw.rectangle((round(xx),round(yy),round(xx+pixel-0.05),round(yy+pixel-0.05)),fill=fill)


def icon_image(label: str, w: int, h: int, coloured: bool):
    from PIL import Image, ImageDraw
    # Image dimensions are native to the BNTX texture; never resize existing atlas slots.
    mode = 'RGBA' if coloured else 'L'
    im = Image.new(mode, (w, h), (0,0,0,0) if coloured else 0)
    draw = ImageDraw.Draw(im)
    label = label.upper()
    tw = max(1, len(label)*6-1)
    if coloured:
        size = min(w,h)*0.9
        bw = max(size*0.9, min(w*0.92, size * min(2.1, (tw+6)/12)))
        bh = min(h*0.84, size*0.80)
        cx,cy=w/2,h/2
        box=(round(cx-bw/2),round(cy-bh/2),round(cx+bw/2),round(cy+bh/2))
        # The in-game ocarina note is a light keycap with darker print and a subtle border.
        draw.rounded_rectangle(box, radius=max(2,round(bh*.20)), fill=(248,245,238,255), outline=(86,74,58,255), width=max(1, round(bh*0.05)))
        pix = min((bw*0.76)/(tw), (bh*0.56)/7)
        draw_pixels(draw,label,cx-tw*pix/2,cy-7*pix/2,pix,(36,31,26,255))
    else:
        # Monochrome texture labels are drawn as a clean keycap silhouette with interior lettering.
        padw = max(1.0, w*0.06)
        padh = max(1.0, h*0.14)
        x0,y0,x1,y1 = padw,padh,w-padw,h-padh
        r = max(1, round((y1-y0)*0.18))
        draw.rounded_rectangle((x0,y0,x1,y1), radius=r, fill=255)
        inset = max(1.0, min(w,h)*0.08)
        draw.rounded_rectangle((x0+inset,y0+inset,x1-inset,y1-inset), radius=max(1, r-round(inset*0.6)), fill=0)
        pix = min(((x1-x0)*0.72)/(tw), ((y1-y0)*0.50)/7)
        draw_pixels(draw,label,(w-tw*pix)/2,(h-7*pix)/2,pix,255)
    return im


def vector_keycap(label: str, width: float, bbox, glyph_set, private, global_subrs):
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    pen = T2CharStringPen(width, glyph_set)
    x0,y0,x1,y1 = bbox
    ww,hh = x1-x0,y1-y0
    x0 += 0.06*ww; y0 += 0.10*hh
    ww *= 0.88; hh *= 0.78

    def polygon(points):
        if len(points) < 3:
            return
        pen.moveTo(points[0])
        for pt in points[1:]:
            pen.lineTo(pt)
        pen.closePath()

    def rectangle(a,b,c,d):
        if c <= a or d <= b:
            return
        polygon([(a,b),(c,b),(c,d),(a,d)])

    def chamfer_box(a,b,c,d,r):
        r = max(0, min(r, (c-a)/2, (d-b)/2))
        polygon([(a+r,b),(c-r,b),(c,b+r),(c,d-r),(c-r,d),(a+r,d),(a,d-r),(a,b+r)])

    # A slightly softer keyboard-style keycap outline.
    chamfer = min(ww,hh) * 0.10
    outer = (x0, y0, x0+ww, y0+hh)
    inner_inset = min(ww,hh) * 0.085
    chamfer_box(*outer, chamfer)
    inner = (outer[0]+inner_inset, outer[1]+inner_inset, outer[2]-inner_inset, outer[3]-inner_inset)
    chamfer_box(*inner, max(0, chamfer-inner_inset*0.55))

    label = label.upper()
    tw = max(1, 6*len(label)-1)
    usable_w = inner[2]-inner[0]
    usable_h = inner[3]-inner[1]
    pixel = min(usable_w*0.78/tw, usable_h*0.56/7)
    ox = inner[0] + (usable_w - tw*pixel)/2
    oy = inner[1] + (usable_h - 7*pixel)/2
    for k,ch in enumerate(label):
        glyph = GLYPHS.get(ch, GLYPHS['?'])
        for row,line in enumerate(glyph):
            for col,c in enumerate(line):
                if c == '1':
                    x = ox + (6*k + col) * pixel
                    # Font coordinates rise upwards, so bitmap rows must be flipped vertically.
                    y = oy + (6 - row) * pixel
                    rectangle(x, y, x + pixel*0.86, y + pixel*0.86)
    return pen.getCharString(private=private, globalSubrs=global_subrs)


def make_font(game_font: bytes, labels: dict[str,str]) -> bytes:
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    key, raw = unwrap(game_font)
    font = TTFont(io.BytesIO(raw))
    if 'CFF ' not in font:
        raise ValueError('Unsupported game font: missing CFF outlines')
    gset=font.getGlyphSet(); cmap=font.getBestCmap()
    chars=font['CFF '].cff.topDictIndex[0].CharStrings
    for name,cp in zip(BUTTONS,CODES):
        gname = cmap.get(cp)
        if not gname:
            print(f'  Warning: game font has no U+{cp:04X}; cannot replace {name}')
            continue
        bp = BoundsPen(gset)
        gset[gname].draw(bp)
        if bp.bounds:
            box = bp.bounds
        else:
            w=font['hmtx'][gname][0]
            box=(w*.15,-w*.15,w*.85,w*.65)
        advance=font['hmtx'][gname][0]
        chars[gname] = vector_keycap(labels[name],advance,box,gset,chars[gname].private,chars[gname].globalSubrs)
    out=io.BytesIO()
    font.save(out)
    return wrap(key,out.getvalue())


def unwrap(blob):
    key = struct.unpack_from('<I',blob,0)[0] ^ MAGIC
    declared = struct.unpack('>I',struct.pack('<I',struct.unpack_from('<I',blob,4)[0]^key))[0]
    body=b''.join(struct.pack('<I',w^key) for w in struct.unpack_from(f'<{(len(blob)-8)//4}I',blob,8))
    if declared > len(body): raise ValueError('Corrupted BFOTF container')
    return key, body[:declared]


def wrap(key,otf):
    original=len(otf)
    padded=otf+b'\0'*((-original)%4)
    header = struct.pack('<II',MAGIC^key,struct.unpack('<I',struct.pack('>I',original))[0]^key)
    return header+b''.join(struct.pack('<I',w^key) for w in struct.unpack(f'<{len(padded)//4}I',padded))


def zs_dictionary(romfs: Path):
    import zstandard
    b=zstandard.ZstdDecompressor().decompressobj().decompress((romfs/'Pack/ZsDic.pack.zs').read_bytes())
    data,=struct.unpack_from('<I',b,12)
    hl,=struct.unpack_from('<H',b,4)
    n,=struct.unpack_from('<H',b,hl+6)
    names=hl+12+16*n+8
    for i in range(n):
        attr,start,end=struct.unpack_from('<III',b,hl+12+16*i+4)
        o=names+(attr&0xffffff)*4
        if b[o:b.index(b'\0',o)]==b'zs.zsdic':
            return b[data+start:data+end]
    raise ValueError('Could not find the game zstd dictionary')


def read_zs(romfs: Path, file: Path, dictionary: bytes):
    import zstandard
    ctx=zstandard.ZstdDecompressor(dict_data=zstandard.ZstdCompressionDict(dictionary))
    return ctx.decompressobj().decompress((romfs/file).read_bytes())


def resource_table(romfs: Path, dictionary: bytes, old_size: int, new_size: int):
    directory=romfs/RESOURCE_DIR
    paths=sorted(directory.glob('ResourceSizeTable.*.rsizetable.zs'))
    if not paths: raise FileNotFoundError(f'Missing resource size table under {directory}')
    path=paths[0]
    raw=bytearray(read_zs(romfs,path.relative_to(romfs),dictionary))
    if raw[:6]!=b'RESTBL': raise ValueError('Unknown resource size table format')
    count,=struct.unpack_from('<I',raw,14)
    crc=zlib.crc32(str(FONT).replace('\\','/').removesuffix('.zs').encode())
    for i in range(count):
        at=22+8*i
        h,size=struct.unpack_from('<II',raw,at)
        if h==crc:
            need=new_size+size-old_size
            if need>size:
                struct.pack_into('<I',raw,at+4,need)
            return path.relative_to(romfs),bytes(raw)
    raise ValueError('Game font not present in the resource size table')


def bntx_textures(b):
    count,=struct.unpack_from('<I',b,0x24)
    info,=struct.unpack_from('<Q',b,0x28)
    out={}
    for i in range(count):
        p,=struct.unpack_from('<Q',b,info+8*i)
        no,=struct.unpack_from('<Q',b,p+0x60)
        nl,=struct.unpack_from('<H',b,no)
        fmt,=struct.unpack_from('<I',b,p+0x1C)
        w,h=struct.unpack_from('<II',b,p+0x24)
        bh,=struct.unpack_from('<I',b,p+0x34)
        mips,=struct.unpack_from('<Q',b,p+0x70)
        data,=struct.unpack_from('<Q',b,mips)
        out[b[no+2:no+2+nl].decode()]=(fmt,w,h,1<<bh,data)
    return out


def gob_offset(x,y,gobs,pitch):
    a=(y//(8*gobs))*512*gobs*pitch+(x//64)*512*gobs+(y%(8*gobs)//8)*512
    return a+((((x&63)>>5)<<8)|(((y&7)>>2)<<7)|(((x&31)>>4)<<6)|(((y>>1)&1)<<5)|((y&1)<<4)|(x&15))


def encode_bc4(im):
    # Minimal valid BC4 endpoint/interpolation encoder (no numpy dependency).
    im=im.convert('L')
    if im.width%4 or im.height%4: raise ValueError('Texture dimensions must be multiples of four')
    out=bytearray()
    px=im.load()
    for by in range(0,im.height,4):
        for bx in range(0,im.width,4):
            v=[px[bx+x,by+y] for y in range(4) for x in range(4)]
            hi=max(v);lo=min(v);span=max(hi-lo,1)
            bits=0
            for k,p in enumerate(v):
                t=round((p-lo)*7/span) if hi>lo else 7
                code=0 if t==7 else (1 if t==0 else 8-t)
                bits|=code<<(3*k)
            out+=bytes((hi,lo))+bits.to_bytes(6,'little')
    return bytes(out)


def encode_astc(im,srgb):
    import astc_encoder as a
    cfg=a.ASTCConfig(a.ASTCProfile.LDR_SRGB if srgb else a.ASTCProfile.LDR,4,4,1,a.ASTCQualityPreset.THOROUGH)
    ctx=a.ASTCContext(cfg)
    return ctx.compress(a.ASTCImage(a.ASTCType.U8,im.width,im.height,1,im.tobytes()),a.ASTCSwizzle.from_str('RGBA'))


def make_textures(base: bytes, labels: dict[str,str]) -> tuple[bytes,int]:
    from PIL import Image
    b=bytearray(base)
    tex=bntx_textures(b)
    changed=0
    for name,key in (list(NOTE_TEXTURES.items())+list(LETTER_TEXTURES.items())):
        if name not in tex:
            print(f'  Warning: no texture {name} in the game; skipped')
            continue
        fmt,w,h,gobs,data=tex[name]
        bpe=16 if fmt>>8==0x2D else 8
        # Same BNTX format selection as Hookshot's nx2/prompt_assets.py:
        # ASTC (0x2Dxx) or 8-byte BC4 blocks for these named UI textures.
        # Textures are encoded block-linear; every native 4x4 block is overwritten in-place.
        bw,bh=(w+3)//4,(h+3)//4
        im=icon_image(labels[key],w,h,name in NOTE_TEXTURES)
        expanded=Image.new(im.mode,(bw*4,bh*4))
        expanded.paste(im,(0,0))
        encoded=encode_astc(expanded.convert('RGBA'),(fmt&0xff)==6) if bpe==16 else encode_bc4(expanded)
        pitch=(bw*bpe+63)//64
        if len(encoded)!=bw*bh*bpe: raise AssertionError(f'Bad encoded length for {name}')
        for yy in range(bh):
            for xx in range(bw):
                offset=data+gob_offset(xx*bpe,yy,gobs,pitch)
                start=(yy*bw+xx)*bpe
                if offset+bpe>len(b): raise ValueError(f'Out-of-bounds texture {name}')
                b[offset:offset+bpe]=encoded[start:start+bpe]
        changed+=1
    return bytes(b),changed


def atomic_write(dst:Path,data:bytes):
    dst.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=dst.name+'.',suffix='.tmp',dir=dst.parent,delete=False) as f:
        tmp=Path(f.name)
        try:
            f.write(data)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    tmp.replace(dst)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Generate actual in-game keyboard prompts as a Hookshot RomFS mod.')
    parser.add_argument('--game',type=Path,required=True,help='Game directory containing hookshot_options.ini and romfs/')
    parser.add_argument('--romfs',type=Path,help='Override path to the extracted original game RomFS')
    parser.add_argument('--both',action='store_true',help='Show both bindings (E/SHIFT); smaller glyphs')
    parser.add_argument('--font-only',action='store_true',help='Only change the text prompt font, not texture-based HUD icons')
    a=parser.parse_args(argv)
    game=a.game.resolve()
    romfs=(a.romfs or game/'romfs').resolve()
    if not (romfs/FONT).exists():
        parser.error(f'No game RomFS found at {romfs}. Pass --romfs with your extracted RomFS folder.')
    mod=game/'mods'/'99-Keyboard-Prompts'/'romfs'
    labels=keyboard_bindings(game/'hookshot_options.ini',a.both)
    # Rebuilding and compressing the huge UI atlas for every launch would be
    # wasteful. Regenerate only for changed bindings, mode, assets or script.
    fingerprint = hashlib.sha256()
    fingerprint.update(json.dumps(labels,sort_keys=True).encode())
    fingerprint.update(bytes((int(a.both),int(a.font_only))))
    fingerprint.update(Path(__file__).read_bytes())
    for source in (romfs/FONT,romfs/TEX,romfs/'Pack/ZsDic.pack.zs'):
        if source.exists():
            st=source.stat()
            fingerprint.update(str((source,st.st_size,st.st_mtime_ns)).encode())
    tables=sorted((romfs/RESOURCE_DIR).glob('ResourceSizeTable.*.rsizetable.zs'))
    for source in tables:
        st=source.stat()
        fingerprint.update(str((source,st.st_size,st.st_mtime_ns)).encode())
    digest=fingerprint.hexdigest()
    state_file=mod.parent/'keyboard_mod_state.json'
    font_out=mod/FONT
    tex_out=mod/TEX
    table_present=list((mod/RESOURCE_DIR).glob('ResourceSizeTable.*.rsizetable.zs'))
    if state_file.exists() and font_out.exists() and (a.font_only or tex_out.exists()) and table_present:
        try:
            if json.loads(state_file.read_text(encoding='utf-8')).get('fingerprint')==digest:
                print('Keyboard prompt mod already matches your current bindings; no rebuild needed.')
                return 0
        except (ValueError,OSError): pass
    print('Keyboard bindings:')
    for k,v in labels.items(): print(f'  {k:>5}: {v}')
    print('Reading original RomFS and its zstd dictionary...')
    dictionary=zs_dictionary(romfs)
    original=read_zs(romfs,FONT,dictionary)
    newfont=make_font(original,labels)
    path,table=resource_table(romfs,dictionary,len(original),len(newfont))
    import zstandard
    compressor=zstandard.ZstdCompressor(level=3)
    files=[(FONT,compressor.compress(newfont)),(path,compressor.compress(table))]
    if not a.font_only:
        print('Patching the 10 keyboard HUD and ocarina textures (may use substantial memory)...')
        atlas=read_zs(romfs,TEX,dictionary)
        patched,n=make_textures(atlas,labels)
        if n==0: raise RuntimeError('No compatible in-game textures found: will not install a misleading HUD mod')
        files.append((TEX,compressor.compress(patched)))
        print(f'  Replaced {n} game textures')
    # Prepare every compressed output before touching an existing installed mod.
    for p,content in files:
        print(f'  Writing {p} ({len(content)/1024/1024:.1f} MiB)')
        atomic_write(mod/p,content)
    if a.font_only and tex_out.exists():
        tex_out.unlink()  # a previous full install should not leave stale texture prompts
    atomic_write(state_file,json.dumps({'fingerprint':digest,'bindings':labels},indent=2).encode())
    print(f'Installed REAL RomFS mod at: {mod.parent}')
    print('The game loads prompts at startup. Rerun before your next launch after changing bindings.')
    return 0


if __name__=='__main__':
    try: sys.exit(main())
    except KeyboardInterrupt:
        sys.exit('Cancelled')
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(f'Error: {e}')
