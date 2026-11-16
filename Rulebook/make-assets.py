"""Turns the colour card art into pure black line art for the black-and-white rulebook.

    python3 make-assets.py        (needs Pillow)

Output goes to assets/ as black-on-transparent PNGs, so nothing prints as grey.
"""
import os
from PIL import Image, ImageChops, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'GtR', 'GtR', 'Images')
OUT = os.path.join(HERE, 'assets')


def line_art(path, scale, outline):
    """Black wherever the art is opaque and not white. With outline=True, white shapes
    (the eagle's head, the banner) keep a thin black contour so they survive on white paper."""
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


os.makedirs(OUT, exist_ok=True)
for role in ['Laborer', 'Craftsman', 'Architect', 'Legionary', 'Patron', 'Merchant']:
    line_art(os.path.join(SRC, 'RoleIcons', role + '.png'), 4, False).save(os.path.join(OUT, role + '.png'), optimize=True)
line_art(os.path.join(SRC, 'Misc', 'GloryToRome.png'), 4, True).save(os.path.join(OUT, 'Eagle.png'), optimize=True)
