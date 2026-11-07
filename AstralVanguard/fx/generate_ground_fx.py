"""Gravity Well ground effect: AVWELLG.BAM (animated vortex, played by avwell.pro as its projectile animation).
   Run:  python generate_ground_fx.py   (needs Pillow). Tweak the constants below and re-run."""
import struct, math, os
from PIL import Image
OUT = os.path.dirname(os.path.abspath(__file__))
W, H = 480, 360                  # frame size; the AoE is 15 ft = 256 x 192 px radius, the art sits just inside it
LOOP_FRAMES = 32                 # slow the three-arm vortex while keeping its 120-degree loop seamless
FRAME_RATE = 15

# ---- fixed palette (index 0 = transparent) ----
PAL = [(5,6,10),(7,8,13),(9,10,16),(11,12,19),(13,14,22),(15,16,25),(17,18,28),(19,20,31),
       (21,22,34),(23,24,37),(25,26,40),(27,28,43),(29,30,46),(31,32,49),(34,35,53),
       (37,38,57),(40,41,61),(43,44,65),(46,47,69),(50,51,74),(54,55,79),(59,60,85),
       (65,66,92),(73,74,101)]
BAYER_4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))

def frame(scale, rot, fade=1.0):
    cx, cy = (W - 1) / 2, (H - 1) / 2
    rx, ry = (W / 2 - 25) * scale, (H / 2 - 32) * scale
    angle = math.radians(rot)
    ix, rgba = [], bytearray()
    for y in range(H):
        ny = (y - cy) / ry
        for x in range(W):
            nx = (x - cx) / rx
            r = math.sqrt(nx * nx + ny * ny)
            if r >= 1.0:
                coverage, brightness = 0.0, 0.0
            else:
                theta = math.atan2(ny, nx)
                log_r = math.log(max(r, 0.14))
                phase = 3 * (theta - angle - 1.9 * log_r)
                arm = max(0.0, math.cos(phase)) ** 2
                disk = math.exp(-((r - 0.64) / 0.20) ** 2)
                photon_ring = math.exp(-((r - 0.31) / 0.035) ** 2)
                outer_fade = max(0.0, min(1.0, (1.0 - r) / 0.16))
                approaching_side = 0.65 + 0.35 * max(0.0, math.cos(theta - angle))

                if r < 0.1425:
                    coverage, brightness = 0.92, 0.015
                else:
                    coverage = 0.20 * disk + 0.42 * disk * arm
                    coverage += 0.42 * photon_ring * approaching_side
                    coverage += 0.12 * math.exp(-((r - 0.84) / 0.09) ** 2) * arm
                    coverage *= outer_fade * fade
                    brightness = 0.08 + 0.30 * disk + 0.30 * disk * arm
                    brightness += 0.28 * photon_ring * approaching_side
                    brightness *= outer_fade

            threshold = (BAYER_4[y % 4][x % 4] + 0.5) / 16
            if coverage <= threshold:
                ix.append(0)
                rgba.extend((0, 0, 0, 0))
                continue

            palette_index = min(len(PAL) - 1, round(brightness * (len(PAL) - 1)))
            ix.append(palette_index + 1)
            rgba.extend((*PAL[palette_index], 255))

    return ix, Image.frombytes("RGBA", (W, H), bytes(rgba))

def write_bam(path, frames, cycles):
    nf, nc = len(frames), len(cycles)
    of = 24; op = of + 12*nf + 4*nc; ol = op + 1024
    lookup = [i for c in cycles for i in c]
    dstart = ol + 2*len(lookup)
    pal = bytearray(1024); pal[0:4] = bytes([0,255,0,0])
    for i, c in enumerate(PAL): pal[(i+1)*4:(i+1)*4+4] = bytes([c[2], c[1], c[0], 255])
    ent = b""; datas = []; off = dstart
    for ix in frames:
        out = bytearray(); i = 0
        while i < len(ix):
            if ix[i] == 0:
                j = i
                while j < len(ix) and ix[j] == 0 and j-i < 256: j += 1
                out += bytes([0, j-i-1]); i = j
            else: out.append(ix[i]); i += 1
        ent += struct.pack("<HHhhI", W, H, W//2, H//2, off); datas.append(bytes(out)); off += len(out)
    cyc = b"".join(struct.pack("<HH", len(c), sum(len(x) for x in cycles[:k])) for k, c in enumerate(cycles))
    blob = b"BAM V1  " + struct.pack("<HBBIII", nf, nc, 0, of, op, ol) + ent + cyc + bytes(pal) + \
           b"".join(struct.pack("<H", i) for i in lookup) + b"".join(datas)
    open(path, "wb").write(blob)

if __name__ == "__main__":
    frames, prev = [], []
    for k in range(LOOP_FRAMES): ix, im = frame(1.0, k*120/LOOP_FRAMES); frames.append(ix); prev.append(im)
    cycles = [list(range(len(frames)))]      # one looping cycle (used by the projectile's trap-visible animation)
    bam_path = os.path.join(OUT, "avwellg.bam")
    write_bam(bam_path, frames, cycles)
    sheet = Image.new("RGBA", (W//2*4, H//2*2), (70,70,70,255))
    preview_frames = [prev[i * LOOP_FRAMES // 8] for i in range(8)]
    for i, im in enumerate(preview_frames):
        sheet.alpha_composite(im.resize((W//2, H//2), Image.LANCZOS), ((i%4)*(W//2), (i//4)*(H//2)))
    sheet.convert("RGB").save(os.path.join(OUT, "avwellg_preview.png"))
    print("frames", len(frames), "BAM bytes", os.path.getsize(bam_path))
