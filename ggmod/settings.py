import os

HOME = os.getenv("HOME", os.getenv("USERPROFILE"))
XDG_CACHE_DIR = os.getenv("XDG_CACHE_HOME", os.path.join(HOME, ".cache"))
XDG_CONF_DIR = os.getenv("XDG_CONFIG_HOME", os.path.join(HOME, ".config"))

CACHE_DIR = os.path.join(XDG_CACHE_DIR, "ggmod")
CONF_DIR = os.path.join(XDG_CACHE_DIR, "ggmod")

# MODULE_DIR = os.path.dirname(__file__)
MODS_DIR = os.path.join(CACHE_DIR, "mods")
DOWNLOAD_DIR = os.path.join(CACHE_DIR, "downloads")
GAME_MOD_DIR = f"{HOME}/.steam/debian-installation/steamapps/common/GUILTY GEAR STRIVE/RED/Content/Paks/~mods"
