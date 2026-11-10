# Hookshot Keyboard Prompts

**Keyboard and mouse button prompts for the PC port of *The Legend of Zelda: Ocarina of Time* (Switch 2 remake).**

This mod replaces the game's Nintendo-style button icons with the keys you actually use in [Hookshot](https://github.com/NotRexed/Hookshot). Instead of placing a separate overlay on top of the game, it generates replacement **RomFS assets** for the in-game interface: dialogue prompts, button hints, and supported HUD textures.

Prompts are generated from your existing `hookshot_options.ini`, so there is no separate keybind list to maintain. Change your controls in Hookshot, rebuild the mod, and the new prompts will appear the next time you launch the game.

> **Note:** The game loads these assets at startup. Keybind changes made while playing cannot update the in-game icons until the mod is rebuilt and Hookshot is restarted.

## Screenshots

### In-game prompts

![Keyboard prompts in Hookshot gameplay](https://github.com/user-attachments/assets/dcab7149-da5b-44dd-a15c-e603abc0c72e)

### System menu and control guide

![Keyboard prompt replacements in the Hookshot System menu](https://github.com/user-attachments/assets/bb10631a-3827-4ba2-9d02-190ebd6c1f61)

*Screenshots were captured during development. The RomFS replacements have been loaded successfully in-game, but the final keycap appearance is still being refined; earlier builds have shown mirrored glyphs or filled keycaps.*

## Features

- **Actual in-game prompts.** Replaces supported button glyphs in the game's font and UI texture atlas; no separate on-screen overlay is needed.
- **Uses your keybinds.** Reads keyboard and mouse assignments directly from `hookshot_options.ini`, including custom controls.
- **Supports mouse buttons.** Displays labels such as `LMB`, `RMB`, `MMB`, `M4`, and `M5`.
- **Optional dual bindings.** Show the first assigned key by default, or use `--both` to show both keys assigned to a button.
- **Automatic rebuilding between launches.** The included launcher checks for changed bindings and regenerates the assets only when needed.
- **No original game assets distributed.** All replacement files are produced locally using your own extracted game files.

## Requirements

- A working installation of [Hookshot](https://github.com/NotRexed/Hookshot) on Windows.
- The game's original, extracted **`romfs` directory**, retained alongside Hookshot or accessible at another path.
- **Python 3.10 or later**, with `pip` available. Download it from [python.org](https://www.python.org/downloads/).
- Enough free space and memory to process the game's UI texture atlas, which can be large when decompressed.

The installer handles the Python packages in `requirements.txt`: FontTools, Pillow, zstandard, and astc-encoder-py.

## Installation

1. **Close Hookshot** before making any changes. Backing up your saves and settings first is recommended.
2. Download this repository using **Code → Download ZIP**, or clone it with Git.
3. Extract the files anywhere convenient, including within your Hookshot game directory.
4. Run **`INSTALL.bat`**.
5. When prompted, select the folder containing `hookshot.exe` and `hookshot_options.ini`.
6. Once generation completes, start Hookshot normally.

The installer reads your existing keybinds and builds the mod at:

```text
Hookshot/
└── mods/
    └── 99-Keyboard-Prompts/
        └── romfs/
            ├── Font2/
            ├── UI/
            └── System/
```

Your original game assets are used as inputs and are not overwritten. The generator writes replacement files into Hookshot's `mods` directory.

### Keeping prompts in sync with your controls

Use **`PLAY_WITH_KEYBOARD_PROMPTS.bat`** instead of launching Hookshot directly. It checks the saved bindings, rebuilds the mod if required, and then starts the game.

If you change a keybind through **Insert → Controls** while playing, exit the game and launch it again through the batch file. The updated key will then be reflected in the generated prompts.

This is an **update between launches**, not live replacement during gameplay.

## Manual installation and options

You can run the generator yourself from a terminal:

```powershell
python -m pip install -r requirements.txt
python build_keyboard_mod.py --game "C:\Games\Hookshot"
```

If your extracted RomFS is stored elsewhere, specify its location:

```powershell
python build_keyboard_mod.py --game "C:\Games\Hookshot" --romfs "D:\MyGame\romfs"
```

Two optional arguments are available:

| Option | Description |
| --- | --- |
| `--both` | Display both bindings for a button, for example `E/ENTER`. Longer labels may appear smaller. |
| `--font-only` | Generate text-based button glyphs without rebuilding the UI texture atlas. Faster, but some HUD icons remain unchanged. |

Each button normally displays its **first** configured key. For example, `key_a=69,13` uses `E` unless you run the generator with `--both`.

## What the mod replaces

Hookshot's button prompts come from more than one kind of asset. This generator currently handles:

| Game element | Support |
| --- | --- |
| Dialogue button icons and contextual button hints | Supported through the game's icon font |
| Ocarina note button textures | Supported |
| A/B/X/Y letter textures in the shared UI atlas | Supported |
| Full controller illustration in the System menu | Not replaced |
| Every custom-made menu graphic and layout | Not fully supported |
| Changing prompts immediately during gameplay | Not supported |

The game also draws certain elements using fixed layouts and controller artwork. These may continue to resemble a controller even when their associated prompts have been replaced.

## How it works

The generator reads the current Windows virtual-key codes from `hookshot_options.ini`, then builds two types of replacement assets from your original RomFS:

1. **Font glyphs:** The game's `External` BFOTF font contains special button-icon characters. The generator replaces their outlines with keyboard-style keycaps labelled according to your bindings.
2. **UI textures:** Supported button textures in the game's `Common` BNTX atlas are redrawn, encoded back into their original texture formats, and placed in a replacement atlas.

Where necessary, it also updates the game's resource size table to accommodate the modified font. Hookshot loads these files using its existing RomFS mod support; no executable patch or external overlay is required.

Changes are not applied to the game's original files. A hash of the relevant inputs is used to avoid rebuilding unchanged assets.

## Troubleshooting

**The game still shows Nintendo button icons.** Make sure `INSTALL.bat` completed without an error, restart Hookshot, and check `hookshot_log.txt` to confirm the mod was discovered. Verify that the generated files exist under `mods/99-Keyboard-Prompts/romfs/`.

**My new keybind is not showing.** The game caches the font and UI textures at startup. Close Hookshot and use `PLAY_WITH_KEYBOARD_PROMPTS.bat` to regenerate the mod before launching again.

**The wrong key appears.** Check the corresponding `key_...` entry in `hookshot_options.ini`. The first binding is shown unless `--both` is enabled.

**The icons look wrong, are upside down, or appear as white squares.** Earlier builds have had font-outline rendering issues. Rebuild using the latest generator, restart the game, and check for another mod replacing the same font, texture atlas, or resource size table. If the issue persists, disable the mod as described below and include a screenshot and relevant `hookshot_log.txt` lines in a bug report.

**Another UI mod conflicts.** Two RomFS mods cannot independently replace the same complete texture atlas or font without an asset merge. Hookshot's mod load order determines which replacement is used.

**Generation uses a lot of memory or takes a while.** The original UI atlas is large and must be decompressed and processed. Try `--font-only` if you only need the text-based prompts.

### Uninstalling

Close the game, then either delete `mods/99-Keyboard-Prompts/` or rename it to `mods/-99-Keyboard-Prompts/`. Hookshot ignores mod directories whose names begin with a hyphen.

Your original RomFS, saves, and settings do not need to be restored, because the generator does not modify them.

## Contributing

Bug reports and contributions are welcome. For rendering issues, please include your Hookshot version, the relevant `hookshot_log.txt` messages, your key mappings (with any private information removed), and a screenshot where possible.

Please **do not upload copyrighted game assets**, including extracted fonts, texture atlases, or RomFS files, when opening an issue or pull request.

## Credits and licence

This project builds upon the technical work in [NotRexed/Hookshot](https://github.com/NotRexed/Hookshot), particularly its input-binding, RomFS mod-loading, font-prompt, and texture-handling implementations. Thanks to its contributors for making the PC port and its modding support possible.

The **mod generator** is released under the **GNU General Public License v3.0 or later (`GPL-3.0-or-later`)**. See [LICENSE](LICENSE) for the full terms. Third-party Python dependencies retain their respective licences.

This repository does not contain or distribute Nintendo game data. Users must supply their own compatible game files. This is an unofficial community project and is not affiliated with, endorsed by, or maintained by Nintendo or the Hookshot developers.
