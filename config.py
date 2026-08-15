"""Configuration file for ROM Migrator."""

# Folder mapping: Anbernic ROM folders -> Knulli/Batocera folders
# Based exclusively on official documentation:
# https://wiki.batocera.org/systems
ANBERNIC_TO_KNULLI = {
    "A2600": "atari2600",
    "A5200": "atari5200",
    "A7800": "atari7800",
    "AMIGA": "amiga",
    "ATARIST": "atarist",
    "ATOMISWAVE": "atomiswave",
    "C64": "c64",
    "CPS1": "fbneo",
    "CPS2": "fbneo",
    "CPS3": "fbneo",
    "DOS": "dos",
    "DREAMCAST": "dreamcast",
    "EASYRPG": "easyrpg",
    "FBNEO": "fbneo",
    "FC": "nes",
    "FDS": "fds",
    "GB": "gb",
    "GBA": "gba",
    "GBC": "gbc",
    "GG": "gamegear",
    "GW": "gameandwatch",
    "LYNX": "lynx",
    "MAME": "mame",
    "MD": "megadrive",
    "MDCD": "megacd",
    "MSX": "msx",
    "N64": "n64",
    "NAOMI": "naomi",
    "NDS": "nds",
    "NEOCD": "neogeocd",
    "NEOGEO": "neogeo",
    "NGP": "ngp",
    "OPENBOR": "openbor",
    "PCE": "pcengine",
    "PCECD": "pcenginecd",
    "PICO": "pico",
    "POKE": "pokemini",
    "PORTS": "ports",
    "PS": "psx",
    "PSP": "psp",
    "SATURN": "saturn",
    "SCUMMVM": "scummvm",
    "SEGA32X": "sega32x",
    "SFC": "snes",
    "SMS": "mastersystem",
    "VB": "virtualboy",
    "VIC20": "vic20",
    "WS": "wswan",
}

# Systems that map to a single folder (require special handling)
MERGE_SYSTEMS = {"fbneo": ["CPS1", "CPS2", "CPS3", "FBNEO"]}

# Common extensions used by multiple systems
COMMON_EXTS = {
    ".zip",
    ".7z",
    ".cue",
    ".bin",
    ".iso",
    ".img",
    ".chd",
    ".mdf",
    ".nrg",
    ".ccd",
    ".sub",
}

# ROM extensions for each system from ANBERNIC_TO_KNULLI
ROM_EXTS = {
    ".a26", ".a52", ".a78",  # Atari
    ".adf", ".adz", ".dms", ".fdi", ".ipf", ".hdf", ".hdz", ".lha",  # Amiga
    ".st", ".msa", ".stx", ".dim",  # Atari ST
    ".crt", ".t64", ".prg", ".p00", ".d64", ".g64",  # C64
    ".exe", ".com", ".bat",  # DOS, ScummVM
    ".cdi", ".gdi",  # Dreamcast
    ".ldb", ".lmu",  # EasyRPG
    ".nes", ".fds",  # NES/FDS
    ".gb", ".gba", ".gbc",  # Game Boy
    ".gg", ".mgw",  # Game Gear, Game & Watch
    ".lnx",  # Lynx
    ".md", ".gen", ".smd",  # Mega Drive
    ".rom", ".mx1", ".mx2",  # MSX
    ".n64", ".z64", ".v64",  # N64
    ".nds",  # NDS
    ".neo",  # Neo Geo
    ".ngp", ".ngc",  # Neo Geo Pocket
    ".pak",  # OpenBOR
    ".pce", ".tg16",  # PC Engine
    ".p8", ".p8.png",  # PICO-8
    ".min",  # Pokemon Mini
    ".sh",  # Ports
    ".img", ".mdf", ".pbp", ".ecm", ".m3u",  # PlayStation
    ".cso",  # PSP
    ".32x", ".a32",  # Sega 32X
    ".sfc", ".smc", ".fig", ".swc",  # Super Nintendo
    ".sms",  # Master System
    ".vb", ".vboy",  # Virtual Boy
    ".ws", ".wsc",  # WonderSwan
}

# Merge common extensions with system extensions
# This creates the final set of all supported extensions
ROM_EXTS_FINAL = ROM_EXTS | COMMON_EXTS
