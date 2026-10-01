"""Usage:
    py tools/clean_image.py INPUT OUTPUT WIDTH HEIGHT [--transparent]

Crops to the right shape, resizes with NO smoothing (keeps pixels sharp),
and with --transparent removes the magenta background."""
import sys

import pygame

TOLERANCE = 90   # raise to 120 if a pink edge is left


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if len(args) != 4:
        print(__doc__)
        return
    src, dst, w, h = args[0], args[1], int(args[2]), int(args[3])

    loaded = pygame.image.load(src)
    image = pygame.Surface(loaded.get_size(), pygame.SRCALPHA)
    image.blit(loaded, (0, 0))

    if "--transparent" in flags:
        print("Removing the magenta background... (this can take a few seconds)")
        for y in range(image.get_height()):
            for x in range(image.get_width()):
                r, g, b, _ = image.get_at((x, y))
                if r > 255 - TOLERANCE and b > 255 - TOLERANCE and g < TOLERANCE:
                    image.set_at((x, y), (0, 0, 0, 0))

    # Center-crop to the wanted shape so nothing gets stretched.
    iw, ih = image.get_size()
    wanted = w / h
    if iw / ih > wanted:
        nw = int(ih * wanted)
        crop = ((iw - nw) // 2, 0, nw, ih)
    else:
        nh = int(iw / wanted)
        crop = (0, (ih - nh) // 2, iw, nh)
    image = image.subsurface(crop).copy()

    image = pygame.transform.scale(image, (w, h))   # nearest neighbor, no blur
    pygame.image.save(image, dst)
    print(f"Saved {dst}  ({w}x{h})")


main()