"""Generate the Riftblade's looping Dimensional Rift ground animation."""
import math
import os
import struct
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))
WIDTH, HEIGHT = 384, 288
FRAME_COUNT = 24
PALETTE_STOPS = (
    (5, 5, 14),
    (21, 13, 48),
    (58, 25, 115),
    (35, 83, 171),
    (34, 178, 221),
    (174, 245, 255),
)
BAYER_4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def build_palette():
    colors = [(0, 0, 0)]
    segments = len(PALETTE_STOPS) - 1
    for index in range(31):
        position = index / 30 * segments
        segment = min(segments - 1, int(position))
        blend = position - segment
        a, b = PALETTE_STOPS[segment], PALETTE_STOPS[segment + 1]
        colors.append(tuple(round(x + (y - x) * blend) for x, y in zip(a, b)))
    return colors


PALETTE = build_palette()


def make_frame(frame_number):
    phase = frame_number * math.tau / FRAME_COUNT
    center_x, center_y = WIDTH / 2, HEIGHT / 2
    radius_x, radius_y = WIDTH * 0.47, HEIGHT * 0.44
    indices = bytearray(WIDTH * HEIGHT)
    rgba = bytearray(WIDTH * HEIGHT * 4)

    for y in range(HEIGHT):
        ny = (y + 0.5 - center_y) / radius_y
        for x in range(WIDTH):
            nx = (x + 0.5 - center_x) / radius_x
            radius = math.hypot(nx, ny)
            if radius > 1.0:
                continue

            angle = math.atan2(ny, nx)
            outer_radius = 0.84 + 0.025 * math.sin(7 * angle - phase)
            outer_ring = math.exp(-((radius - outer_radius) / 0.035) ** 2)
            outer_segments = 0.25 + 0.75 * max(0.0, math.cos(8 * (angle - phase * 0.3)))

            middle_radius = 0.62 + 0.018 * math.sin(5 * angle + phase)
            middle_ring = math.exp(-((radius - middle_radius) / 0.028) ** 2)
            middle_segments = 0.25 + 0.75 * max(0.0, math.cos(6 * (angle + phase * 0.45)))

            inner_ring = math.exp(-((radius - 0.49) / 0.025) ** 2)
            spiral = max(0.0, math.cos(3 * (angle - phase * 0.5) + 11 * (radius - 0.5))) ** 5
            spiral *= math.exp(-((radius - 0.69) / 0.18) ** 2)

            rotated_x = nx * math.cos(phase) - ny * math.sin(phase)
            rotated_y = nx * math.sin(phase) + ny * math.cos(phase)
            crack_center = 0.025 * math.sin(rotated_y * 34 + phase * 2)
            crack_width = 0.014 + 0.006 * (0.5 + 0.5 * math.sin(rotated_y * 57 - phase))
            crack = (
                abs(rotated_x - crack_center) < crack_width
                and abs(rotated_y) < 0.45
                and radius < 0.5
            )

            core = radius < 0.47
            coverage = 0.0
            brightness = 0.0
            if core:
                coverage = 0.78
                brightness = 0.07 + 0.06 * (1.0 - radius / 0.47)
            coverage = max(coverage, outer_ring * outer_segments * 0.9)
            brightness = max(brightness, outer_ring * outer_segments * 0.72)
            coverage = max(coverage, middle_ring * middle_segments * 0.95)
            brightness = max(brightness, middle_ring * middle_segments * 0.88)
            coverage = max(coverage, inner_ring * 0.8)
            brightness = max(brightness, inner_ring * 0.76)
            coverage = max(coverage, spiral * 0.72)
            brightness = max(brightness, spiral * 0.58)
            if crack:
                coverage = 1.0
                brightness = 1.0

            threshold = (BAYER_4[y % 4][x % 4] + 0.5) / 16
            if coverage <= threshold:
                continue

            palette_index = min(31, max(1, round(brightness * 31)))
            indices[y * WIDTH + x] = palette_index
            color = PALETTE[palette_index]
            pixel_offset = (y * WIDTH + x) * 4
            rgba[pixel_offset:pixel_offset + 4] = bytes((*color, 255))

    return indices, Image.frombytes("RGBA", (WIDTH, HEIGHT), bytes(rgba))


def write_bam(path, frames):
    frame_count = len(frames)
    frame_table_offset = 24
    cycles = [list(range(frame_count))]
    palette_offset = frame_table_offset + 12 * frame_count + 4 * len(cycles)
    lookup_offset = palette_offset + 1024
    data_offset = lookup_offset + 2 * frame_count
    encoded_frames = []
    frame_table = bytearray()
    current_offset = data_offset

    for frame in frames:
        encoded = bytearray()
        index = 0
        while index < len(frame):
            if frame[index] == 0:
                end = index
                while end < len(frame) and frame[end] == 0 and end - index < 256:
                    end += 1
                encoded.extend((0, end - index - 1))
                index = end
            else:
                encoded.append(frame[index])
                index += 1
        frame_table.extend(struct.pack(
            "<HHhhI", WIDTH, HEIGHT, WIDTH // 2, HEIGHT // 2, current_offset
        ))
        encoded_frames.append(bytes(encoded))
        current_offset += len(encoded)

    cycle_table = struct.pack("<HH", frame_count, 0)
    palette = bytearray(1024)
    palette[:4] = bytes((0, 255, 0, 0))
    for index, (red, green, blue) in enumerate(PALETTE[1:], 1):
        palette[index * 4:index * 4 + 4] = bytes((blue, green, red, 255))
    lookup_table = b"".join(struct.pack("<H", index) for index in range(frame_count))
    header = b"BAM V1  " + struct.pack(
        "<HBBIII", frame_count, 1, 0, frame_table_offset,
        palette_offset, lookup_offset
    )
    with open(path, "wb") as output:
        output.write(header)
        output.write(frame_table)
        output.write(cycle_table)
        output.write(palette)
        output.write(lookup_table)
        for frame in encoded_frames:
            output.write(frame)


def write_preview(images, path):
    thumb_width, thumb_height = WIDTH // 2, HEIGHT // 2
    sheet = Image.new("RGBA", (thumb_width * 4, thumb_height * 2), (64, 64, 68, 255))
    for index in range(8):
        image = images[index * FRAME_COUNT // 8].resize(
            (thumb_width, thumb_height), Image.Resampling.LANCZOS
        )
        sheet.alpha_composite(image, ((index % 4) * thumb_width, (index // 4) * thumb_height))
    sheet.convert("RGB").save(path)


if __name__ == "__main__":
    rendered = [make_frame(index) for index in range(FRAME_COUNT)]
    write_bam(os.path.join(OUT, "rfdimr.bam"), [frame for frame, _ in rendered])
    write_preview([image for _, image in rendered], os.path.join(OUT, "rfdimr_preview.png"))
    print(f"Generated {FRAME_COUNT} looping frames.")
