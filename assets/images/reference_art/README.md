# BayanSafe reference artwork

These are cropped pieces from the two pixel-art element sheets supplied for
the game. The crops are used directly by the world renderer for character
sprites, buildings, supplies, disaster effects, and the final control-room
scene. They do not replace the approved island map or its walkability data.

- `characters/`: recurring story cast, regional cast, and civilians
- `buildings/`: homes, community buildings, docks, bridge, shelters, and facilities
- `items/`: pickup art for supplies and story objects
- `effects/`: fire, water splash, dust, and other hazard visuals
- `locations/`: world-engine exterior and final control-room interior
- `terrain/` and `hazards/`: reference samples retained for future matching;
  framed terrain thumbnails are not tiled as walkable ground

`tools/extract_reference_art.py` rebuilds these crops from the supplied sheets.
