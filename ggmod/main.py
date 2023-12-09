from argparse import ArgumentParser
from PyPAKParser import PakParser as PP

from ggmod.const import *
from ggmod.settings import *
from ggmod import util

import logging
import shutil
import os
import re

from typing import Dict


def download(mod_urls):
    for url in mod_urls:
        modpage = mods.ModPage(url)

        for mod in modpage:
            archive = mod.download()

        pak_fn, sig_fn = decompress_mod(filename)
        is_mesh_mod, char_id, slot = get_mod_info(pak_fn)
        place_mod(char_id, pak_fn, sig_fn, is_mesh_mod, slot)


def sync(args):
    force = args[0]

    all_files = []
    all_flat_files = []
    for root, _, files in os.walk(GAME_MOD_DIR):
        all_flat_files += files
        all_files += list(map(lambda f: os.path.join(root, f), files))

    if force:
        *_, active_mods = next(os.walk(GAME_MOD_DIR))
        for mod in active_mods:
            os.remove(os.path.join(GAME_MOD_DIR, mod))
            print(f"[!] Removing {os.path.join(GAME_MOD_DIR, mod)}")

    for path, flat_path in zip(all_files, all_flat_files):
        try:
            shutil.copy(path, os.path.join(GAME_MOD_DIR, flat_path))
        except BaseException as e:
            log.warning(e, path, os.path.join(GAME_MOD_DIR, flat_path))
            exit()
        print(f"[*] Copying {path} to {os.path.join(GAME_MOD_DIR, flat_path)}")


# ggmod download <link>
# ggmod remove <mod>
# ggmod list jacko
# ggmod use jacko skin <mod>
# ggmod use jacko mesh <mod>
# ggmod list nago 1 (slot 1)
# ggmod rename <old> <new>

def parse_args():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help="List of subcommands")

    # Big ol' list of subcommands and their respective arguments/functions
    down_parser = subparsers.add_parser("download",
            help="Download a mod from a gamebanana link")
    down_parser.add_argument("link",
            help="Mod page or download url (taken from browser)")
    down_parser.set_defaults(func=download)

    sync_parser = subparsers.add_parser("sync",
            help="Sync local mods with game directory")
    down_parser.add_argument("-f", "--force", action="store_true",
            help="Completley wipe the in-game mods directory and sync")
    down_parser.set_defaults(func=sync)

    args = parser.parse_args()

    if not any(var(args)):
        parser.error("Must specify an argument such as 'download' or 'sync'")

    return args


def main():
    util.configure_logging()

    util.mkdir(CONF_DIR)
    util.mkdir(DOWNLOAD_DIR)
    util.mkdir(GAME_MOD_DIR)

    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
