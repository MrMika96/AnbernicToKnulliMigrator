# AnbernicToKnulliMigrator

A Python tool to migrate ROM files from Anbernic stock OS to Knulli/Batocera OS.

## Features

- 📂 **Safe copy** - Source files are NOT deleted
- 🔄 **Automatic folder mapping** - Anbernic folders → Knulli folders
- 🎯 **Interactive mode** - Just run and follow prompts
- 📊 **Progress bar** - Shows progress with ETA
- 🛡️ **Permission handling** - Clear error messages and suggestions

## Requirements

- Python 3.6 or higher

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/AnbernicToKnulliMigrator.git
cd AnbernicToKnulliMigrator
```

## Usage

### Interactive Mode (Recommended)

Simply run without arguments:

```bash
python rom_migrator.py
```

The script will guide you through:
1. Select source folder (Anbernic ROMs)
2. Select destination folder (Knulli ROMs)
3. Choose options (dry-run, verbose)

### Command Line Mode

```bash
python rom_migrator.py -s /path/to/anbernic/ROMS -d /path/to/knulli/roms
```

### Options

| Option | Description |
|--------|-------------|
| `-s, --source` | Source folder with Anbernic ROMs |
| `-d, --dest` | Destination folder for Knulli ROMs |
| `--dry-run` | Preview only, no copying |
| `-v, --verbose` | Show every file being copied |
| `-i, --interactive` | Interactive mode with prompts |

### Examples

```bash
# Interactive mode
python main.py

# Quick copy
python main.py -s D:/Anbernic/ROMS -d E:/storage/roms

# Dry run to preview
python main.py -s D:/Anbernic/ROMS -d E:/storage/roms --dry-run -v
```

## Folder Mapping

Anbernic folders are automatically mapped to Knulli/Batocera folders:

| Anbernic | Knulli |
|----------|--------|
| A2600 | atari2600 |
| A5200 | atari5200 |
| A7800 | atari7800 |
| AMIGA | amiga |
| ATARIST | atarist |
| ATOMISWAVE | atomiswave |
| C64 | c64 |
| CPS1 | fbneo |
| CPS2 | fbneo |
| CPS3 | fbneo |
| DOS | dos |
| DREAMCAST | dreamcast |
| EASYRPG | easyrpg |
| FBNEO | fbneo |
| FC | nes |
| FDS | fds |
| GB | gb |
| GBA | gba |
| GBC | gbc |
| GG | gamegear |
| GW | gameandwatch |
| LYNX | lynx |
| MAME | mame |
| MD | megadrive |
| MDCD | megacd |
| MSX | msx |
| N64 | n64 |
| NAOMI | naomi |
| NDS | nds |
| NEOCD | neogeocd |
| NEOGEO | neogeo |
| NGP | ngp |
| OPENBOR | openbor |
| PCE | pcengine |
| PCECD | pcenginecd |
| PICO | pico |
| POKE | pokemini |
| PORTS | ports |
| PS | psx |
| PSP | psp |
| SATURN | saturn |
| SCUMMVM | scummvm |
| SEGA32X | sega32x |
| SFC | snes |
| SMS | mastersystem |
| VB | virtualboy |
| VIC20 | vic20 |
| WS | wswan |

## Troubleshooting

### Permission Denied

**Windows:** Run as Administrator

**Linux/macOS:** Use `sudo`
```bash
sudo python3 rom_migrator.py
```
