from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "static" / "images" / "brand"
SRC = BRAND / "logo-source.png"
LOGO = BRAND / "logo.png"
FAVICON = BRAND / "favicon.png"


def is_background(pixel, threshold=28):
    red, green, blue, _alpha = pixel
    return red <= threshold and green <= threshold and blue <= threshold


def non_black_bbox(image, step=1):
    pixels = image.load()
    width, height = image.size
    min_x, min_y, max_x, max_y = width, height, 0, 0
    found = False
    for y in range(0, height, step):
        for x in range(0, width, step):
            if not is_background(pixels[x, y]):
                found = True
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if not found:
        raise SystemExit("Could not find the circular emblem in logo.png")
    return min_x, min_y, max_x + 1, max_y + 1


def make_square(box, image_size):
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    side = max(width, height)
    extra_x = side - width
    extra_y = side - height
    left -= extra_x // 2
    top -= extra_y // 2
    right = left + side
    bottom = top + side
    max_w, max_h = image_size
    if left < 0:
        right -= left
        left = 0
    if top < 0:
        bottom -= top
        top = 0
    if right > max_w:
        left -= right - max_w
        right = max_w
    if bottom > max_h:
        top -= bottom - max_h
        bottom = max_h
    return (max(0, left), max(0, top), min(max_w, right), min(max_h, bottom))


def punch_black_background(image):
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if is_background((red, green, blue, alpha)):
                pixels[x, y] = (0, 0, 0, 0)


def circular_mask(image):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    inset = 2
    draw.ellipse(
        (inset, inset, image.size[0] - inset - 1, image.size[1] - inset - 1),
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(0.6))
    out = image.copy()
    out.putalpha(mask)
    return out


def main():
    if not SRC.exists():
        raise SystemExit(f"Missing source logo: {SRC}")
    source = Image.open(SRC).convert("RGBA")
    print("source", source.size, source.mode)
    box = non_black_bbox(source)
    pad = 4
    box = (
        max(0, box[0] - pad),
        max(0, box[1] - pad),
        min(source.size[0], box[2] + pad),
        min(source.size[1], box[3] + pad),
    )
    print("bbox", box, "size", box[2] - box[0], box[3] - box[1])
    square = make_square(box, source.size)
    print("square", square)
    cropped = source.crop(square)
    punch_black_background(cropped)
    cropped = circular_mask(cropped)
    cropped.save(LOGO, optimize=True)
    favicon = cropped.resize((256, 256), Image.Resampling.LANCZOS)
    favicon.save(FAVICON, optimize=True)
    print("saved", LOGO, cropped.size)
    print("saved", FAVICON, favicon.size)


if __name__ == "__main__":
    main()
