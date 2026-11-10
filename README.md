# Hookshot — actual in-game keyboard button prompts (RomFS mod generator)

This is **not a desktop overlay**. It generates a real `mods/99-Keyboard-Prompts/romfs/` mod for the [NotRexed/Hookshot](https://github.com/NotRexed/Hookshot) PC port of the Ocarina of Time Switch 2 remake. It changes the **game's** font icon outlines and the game's UI texture atlas, using the keyboard bindings stored in `hookshot_options.ini`.

**The generated files depend on the player's own game files.** No game font, texture atlas, RomFS data, or compiled game is included in this ZIP. You need an installed Hookshot game and its retained `romfs` folder to generate the assets.

## Install on Windows

1. **Close Hookshot**. Back up your saves/settings before modding.
2. Ensure you have **Python 3.10+** installed from [python.org](https://www.python.org/downloads/) with `pip` (select **Add Python to PATH** if offered).
3. Extract this ZIP into a folder alongside your Hookshot installation (putting it *inside* the Hookshot game folder also works).
4. Double-click **`INSTALL.bat`**. If asked, enter the path of the folder containing `hookshot.exe`, `hookshot_options.ini`, and `romfs`.
5. It installs Python dependencies, reads your own RomFS, and builds the mod at `<game folder>/mods/99-Keyboard-Prompts/romfs/`.
6. Start Hookshot normally. The replacement keycaps should appear where the game displays its text button icons, ocarina note buttons and applicable in-game UI key textures.

**For automatic updates between runs:** Launch with `PLAY_WITH_KEYBOARD_PROMPTS.bat`. It checks your current bindings, only regenerates the mod when something changed, and starts Hookshot. If you edited bindings in Hookshot's **Insert → Controls** menu during a session, **exit and launch through this BAT again** to see the new icons.

You can also run manually:

```powershell
python -m pip install -r requirements.txt
python build_keyboard_mod.py --game "C:\Games\Hookshot"
```

If your game's original RomFS isn't at `<game folder>/romfs`, pass it separately:

```powershell
python build_keyboard_mod.py --game "C:\Games\Hookshot" --romfs "D:\MyGame\romfs"
```

Use `--both` to draw both bound keys (e.g. `E/SHIFT`) instead of only the first binding, although labels may be smaller. Use `--font-only` for a quicker build if you only want the text icons, not the texture HUD elements.

## Important limitation — changing bindings during play

This is a **real, loadable RomFS replacement mod**. Hookshot currently only loads RomFS mods and indexes their files at startup; the game reads its button-icon font and UI atlas at startup as well. A RomFS mod cannot make an already-loaded in-game button icon change instantly when the bindings change in Insert → Controls. The regenerated icons become visible **on the next game launch**. The BAT wrapper is the closest possible automatic behaviour without modifying and rebuilding Hookshot's host or injecting unsupported native code.

## Which prompts are affected?

- **Yes:** The button-icons used by in-game dialogue and control prompts (`Font2/Scalable/External...bfotf`).
- **Yes:** Ocarina note button textures (`OcarinaButton...`) and A/B/X/Y UI letter textures (`KeyTexFont...`) in `Common...bntx`.
- **Not yet:** Every bespoke layout or controller picture in the pause menu. The original full controller guide and the Talk ring positions remain; labels within their fonts and selected textures are replaced where applicable.
- **Not live:** Changes to Hookshot's control bindings only appear once the game loads a regenerated mod on the next launch.

When a binding has two entries (`key_a=69,13`), the mod shows the **first** by default; `--both` shows both. Mouse buttons use `LMB`, `RMB`, `MMB`, `M4`, `M5`; other key codes are the Windows virtual-key codes used by Hookshot.

## Uninstall / disable

Close the game and rename `mods/99-Keyboard-Prompts` to `mods/-99-Keyboard-Prompts`, or delete the mod folder. Hookshot ignores mod folders beginning with `-`. No original game files, settings or saves are modified.

## Troubleshooting

- The builder needs the **actual** original `romfs` folder; it does **not** generate anything from a save file or just `hookshot_options.ini`.
- Verify the mod is recognised in `hookshot_log.txt` and that no later-sorting mod replaces the same font/texture files.
- If another texture mod replaces `UI/Layout2Archive/Common.Product.100.Nin_Ounce_NVN2.bntx.zs`, only one complete atlas can be loaded unless the mods are merged.
- If another font or resource size table mod replaces the same paths, they may conflict.
- A texture atlas can be hundreds of MB uncompressed, so the initial generation may require substantial free memory and disk space.
- To check an edited binding, **close and relaunch** with `PLAY_WITH_KEYBOARD_PROMPTS.bat`.

## Implementation / attribution

The paths and file container formats follow the upstream GPL-3.0 Hookshot source: `host/prompts.c`, `host/mods.c`, `nx2/prompt_assets.py`, `host/nn_hid.c`. This independent builder uses the game's CFF icon glyphs and block-linear ASTC/BC4 atlas only as **local input**, never redistributes their assets. It generates 5×7 bitmap-labelled vector and texture keycaps. External dependencies: FontTools, Pillow, python-zstandard and astc-encoder-py. The generator is licensed under GPL-3.0-or-later to maintain compatibility with the upstream implementation it derives technical details from.

**Verification status:** The CFF editing/serialization and BC4/block-linear texture algorithms have been exercised using test assets. Full in-game testing against your exact Hookshot build and copyrighted RomFS was not possible here, so if anything renders incorrectly use `hookshot_log.txt` and disable the mod as above.
