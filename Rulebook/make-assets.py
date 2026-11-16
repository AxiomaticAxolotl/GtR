"""Turns the colour card art into greyscale art for the rulebook.

    python3 make-assets.py        (needs Pillow)

Role icons become solid black silhouettes (they are tiny, so they need the contrast);
the eagle logo keeps its shading. Output goes to assets/ as PNGs with transparency.
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


# Print tones for the eagle logo, keyed by what each colour in the card art is.
EAGLE_TONES = [          # painted in this order, each over the last
    ('feathers', 0x8c),  # light grey wing tiles
    ('white', 0xff),     # head and banner
    ('laurel', 0x55),    # green leaves
    ('ties', 0xc4),      # yellow bindings
    ('lettering', 0x00), # red banner text
]
EAGLE_BODY = 0x14        # everything else: the dark grey body, eye and outlines


def classify(r, g, b):
    if max(r, g, b) - min(r, g, b) > 60:
        if g >= r:
            return 'laurel'
        return 'ties' if g >= 100 else 'lettering'
    lum = (r + g + b) // 3
    return 'white' if lum >= 232 else 'feathers' if lum >= 200 else 'body'


def flat_tones(path, scale):
    """Redraws flat-colour art as flat grey tones with smooth edges: each colour region is
    upscaled as its own mask, so there is no pixel stair-stepping and no halo between tones."""
    im = Image.open(path).convert('RGBA')
    size = (im.width * scale, im.height * scale)

    def smooth(mask):
        return mask.resize(size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale * 0.55)).point(lambda v: 255 if v > 127 else 0)

    px = list(im.get_flattened_data())
    kinds = [classify(r, g, b) if a > 127 else None for r, g, b, a in px]
    silhouette = Image.new('L', im.size)
    silhouette.putdata([255 if k else 0 for k in kinds])
    silhouette = smooth(silhouette)

    grey = Image.new('L', size, EAGLE_BODY)
    for kind, tone in EAGLE_TONES:
        mask = Image.new('L', im.size)
        mask.putdata([255 if k == kind else 0 for k in kinds])
        grey.paste(tone, mask=smooth(mask))
    # A thin dark contour so the white head and banner don't vanish into the page.
    edge = ImageChops.subtract(silhouette, silhouette.filter(ImageFilter.MinFilter(2 * scale + 1)))
    grey.paste(EAGLE_BODY, mask=edge)
    # Soften the outer edge by a pixel so it isn't stair-stepped either.
    return Image.merge('LA', (grey, silhouette.filter(ImageFilter.GaussianBlur(0.8))))


os.makedirs(OUT, exist_ok=True)
for role in ['Laborer', 'Craftsman', 'Architect', 'Legionary', 'Patron', 'Merchant']:
    line_art(os.path.join(SRC, 'RoleIcons', role + '.png'), 4, False).save(os.path.join(OUT, role + '.png'), optimize=True)
flat_tones(os.path.join(SRC, 'Misc', 'GloryToRome.png'), 4).save(os.path.join(OUT, 'Eagle.png'), optimize=True)
