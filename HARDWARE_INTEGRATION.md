# Hardware integration notes

BayanSafe is single-player. The desktop build now accepts a standard Pygame-compatible USB HID joystick and button device as an optional input source. Keyboard controls remain available. The starter mapping is in `data/hardware_profile.example.json` and can be changed in `src/hardware/pygame_controller.py`.

The device drawing identifies a joystick, an LCD, RFID, two large buttons, and two small buttons. It does not identify the controller board, reader, UID output mode, LCD interface/resolution, wiring, or serial message format. Those details are required before a custom serial board or RFID reader can be integrated; the game does not guess pins or accept arbitrary card data.

## Current input mapping

| HID input | Game action |
|---|---|
| Left stick / axes 0 and 1 | Move and navigate menus |
| Button 0 | Confirm / talk |
| Button 1 | Back / pause |
| Button 2 | Previous option / menu item |
| Button 3 | Next option / menu item |
| Keyboard | Full fallback controls |

The two small buttons follow the proposal's previous/next mapping. The large confirm button also talks to nearby characters, so interaction remains a one-button action during play. Buttons can be remapped in the `DEFAULT_BUTTONS` table. The deadzone is adjustable in `PygameController`.

## To connect the project board

1. Confirm the exact board and its USB mode (HID or serial).
2. Confirm joystick axis range and each button's electrical/firmware mapping.
3. For serial devices, publish a sample message for neutral, each direction, each button press/release, and disconnect/reconnect. Then implement a transport adapter that emits the same Pygame key events as the HID adapter.
4. Confirm the LCD model, resolution, color depth, and transport. The game's logical canvas is 320 × 180; a separate display renderer or scaling profile may be needed.
5. Confirm RFID reader model and UID mode. Link the card to a player account through an authenticated enrollment flow; never show a raw UID on the public leaderboard.
6. Test reconnect behavior, held-button release, malformed input, and multiple cards/controllers on the actual device before deployment.

The optional Flask account/RFID service is separate from the game client. Physical RFID login and LCD mirroring are not connected yet.
