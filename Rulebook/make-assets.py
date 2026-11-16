"""Turns the colour card art into greyscale art for the rulebook.

    python3 make-assets.py        (needs Pillow)

Role and card set icons become solid black silhouettes, and the eagle logo is redrawn as it looks on
the box: solid black, with a grey banner. Output goes to assets/ as PNGs with transparency.
"""
import os
from PIL import Image, ImageChops, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'GtR', 'GtR', 'Images')
OUT = os.path.join(HERE, 'assets')


def line_art(path, scale, outline=False):
    """Solid black wherever the art is opaque and not white. With outline=True, white
    shapes keep a thin black contour."""
    im = Image.open(path).convert('RGBA')
    im = im.resize((im.width * scale, im.height * scale), Image.BICUBIC)
    opaque = im.split()[3].filter(ImageFilter.GaussianBlur(scale * 0.75)).point(lambda v: 255 if v > 127 else 0)
    flat = Image.new('RGBA', im.size, (255, 255, 255, 255))
    flat.alpha_composite(im)
    lum = flat.convert('L').filter(ImageFilter.GaussianBlur(scale * 0.6))
    ink = ImageChops.multiply(lum.point(lambda v: 255 if v < 225 else 0), opaque)
    if outline:
        edge = ImageChops.subtract(opaque, opaque.filter(ImageFilter.MinFilter(2 * scale + 1)))
        ink = ImageChops.lighter(ink, edge)
    ink = ink.filter(ImageFilter.GaussianBlur(scale * 0.5)).point(lambda v: 255 if v > 127 else 0)
    black = Image.new('L', im.size, 0)
    return Image.merge('LA', (black, ink))


def from_alpha(path, scale):
    """The card set icons are white shapes on transparency (they sit on dark card art),
    so their shape is the alpha channel: redraw it in black with smoothed edges."""
    alpha = Image.open(path).convert('RGBA').split()[3]
    alpha = alpha.resize((alpha.width * scale, alpha.height * scale), Image.BICUBIC)
    alpha = alpha.filter(ImageFilter.GaussianBlur(scale * 0.4)).point(lambda v: 255 if v > 127 else 0)
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.8))
    box = alpha.getbbox()                       # trim the empty border so it sits tight in a line of text
    return Image.merge('LA', (Image.new('L', alpha.size, 0), alpha)).crop(box)


BANNER_TONE = 0x58  # the box's red banner, as the grey it prints at


def classify(r, g, b, a):
    if a <= 127:
        return None
    if max(r, g, b) - min(r, g, b) > 60:
        return 'lettering' if r > g and g < 100 else 'leaf'   # red text; green laurel and its yellow ties
    return 'white' if (r + g + b) // 3 >= 232 else 'grey'     # head and banner; body, feathers and outlines


def components(kinds, w, h, kind):
    """4-connected regions of one kind, as (pixel indices, bounding box)."""
    seen, out = set(), []
    for start in range(w * h):
        if kinds[start] != kind or start in seen:
            continue
        seen.add(start)
        stack, region = [start], []
        while stack:
            i = stack.pop()
            region.append(i)
            x, y = i % w, i // w
            for n in ((i + 1) if x + 1 < w else -1, (i - 1) if x else -1, i + w if y + 1 < h else -1, i - w if y else -1):
                if n >= 0 and kinds[n] == kind and n not in seen:
                    seen.add(n)
                    stack.append(n)
        xs, ys = [i % w for i in region], [i // w for i in region]
        out.append((region, (min(xs), min(ys), max(xs), max(ys))))
    return out


def eagle(path, scale):
    """Redraws the logo the way it appears on the box: a solid black eagle and laurel over a
    darker banner with white lettering. The card art has a white head and a white banner with
    red text, so those are flipped. Every region is upscaled as its own mask to keep edges smooth."""
    im = Image.open(path).convert('RGBA')
    w, h = im.size
    size = (w * scale, h * scale)
    kinds = [classify(*p) for p in im.get_flattened_data()]

    def mask(indices):
        m = Image.new('L', (w, h))
        data = bytearray(w * h)
        for i in indices:
            data[i] = 255
        m.frombytes(bytes(data))
        return m.resize(size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale * 0.55)).point(lambda v: 255 if v > 127 else 0)

    inside = lambda box, outer: outer[0] <= box[0] and box[2] <= outer[2] and outer[1] <= box[1] and box[3] <= outer[3]
    whites = components(kinds, w, h, 'white')
    head = max((c for c in whites if c[1][3] < h // 2), key=lambda c: len(c[0]))
    lower = sorted((c for c in whites if c[1][1] > h // 2), key=lambda c: -len(c[0]))
    banner, tabs = lower[0], lower[1:3]         # the ribbon and its two folded ends
    bx0, by0, bx1, by1 = banner[1]
    banner_box = (bx0 - 2, by0 - 2, bx1 + 2, by1 + 2)

    ink = [i for i, k in enumerate(kinds) if k == 'leaf']
    band = banner[0] + tabs[0][0] + tabs[1][0]
    for region, box in lower[3:]:
        if inside(box, banner_box):
            band += region                      # counters of the letters
    for region, box in components(kinds, w, h, 'grey'):
        if inside(box, head[1]):
            continue                            # the eye: stays white inside the black head
        if inside(box, banner_box):
            band += region                      # the banner's thin outline
        else:
            ink += region

    ink_mask, band_mask = mask(ink), mask(band)
    # The head goes black too, less a white collar where it meets the body. Opening the ink
    # mask first drops the head's own thin outline, so only the body carves the collar.
    k = 2 * round(scale * 2) + 1
    body = ink_mask.filter(ImageFilter.MinFilter(k)).filter(ImageFilter.MaxFilter(k))
    collar = body.filter(ImageFilter.MaxFilter(2 * round(scale * 2.5) + 1))
    head_mask = ImageChops.subtract(mask(head[0]), collar)
    black = ImageChops.lighter(ink_mask, head_mask)

    grey = Image.new('L', size, BANNER_TONE)
    grey.paste(0, mask=black)
    alpha = ImageChops.lighter(black, band_mask).filter(ImageFilter.GaussianBlur(0.8))
    return Image.merge('LA', (grey, alpha))


os.makedirs(OUT, exist_ok=True)
for role in ['Laborer', 'Craftsman', 'Architect', 'Legionary', 'Patron', 'Merchant']:
    line_art(os.path.join(SRC, 'RoleIcons', role + '.png'), 4, False).save(os.path.join(OUT, role + '.png'), optimize=True)
for card_set in ['Republic', 'Imperium']:
    from_alpha(os.path.join(SRC, 'Misc', card_set + '.png'), 8).save(os.path.join(OUT, card_set + '.png'), optimize=True)
eagle(os.path.join(SRC, 'Misc', 'GloryToRome.png'), 4).save(os.path.join(OUT, 'Eagle.png'), optimize=True)
