from argparse import ArgumentParser

from ggmod.settings import *
from ggmod import util
from ggmod import mods

import logging
import shutil
import os


def download(args):
    for url in args.link:
        modpage = mods.ModPage(url)

        if len(modpage) > 1:
            archives = []

            for i, mod in enumerate(modpage):
                archives.append(mod.download())
                if mod.is_mesh():
                    print(f"[{i+1}] Mesh mod {mod.filename[0]} - {mod.description}")
                else:
                    print(f"[{i+1}] Colour{mod.get_slot()} mod {mod.filename[0]} - {mod.description}")

            choice = int(input("[?] Choice: "))-1
            modpage[choice].select(archives[choice])
        else:
            archives = mod.download()
            mod.select(archives)


def sync(args):
    all_files = []
    all_flat_files = []

    for root, _, files in os.walk(MODS_DIR):
        print(root, files)
        all_flat_files += files
        all_files += list(map(lambda f: os.path.join(root, f), files))

    if args.force:
        *_, active_mods = next(os.walk(GAME_MOD_DIR))
        print(active_mods)
        for mod in active_mods:
            os.remove(os.path.join(GAME_MOD_DIR, mod))
            print(f"[!] Removing {os.path.join(GAME_MOD_DIR, mod)}")

    for path, flat_path in zip(all_files, all_flat_files):
        new_path = os.path.join(GAME_MOD_DIR, flat_path)

        if not os.path.isfile(new_path):
            print(f"[*] Copying {path} to {os.path.join(GAME_MOD_DIR, flat_path)}")
            shutil.copy(path, new_path)


def parse_args():
    """
    ggmod download <link>
    ggmod remove <mod(folder)>
    ggmod list jacko
    ggmod use jacko skin <mod>
    ggmod use jacko mesh <mod>
    ggmod list nago 1 (slot 1)
    ggmod rename <old> <new>
    """

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help="List of subcommands")

    # Big ol' list of subcommands and their respective arguments/functions
    down_parser = subparsers.add_parser("download",
            help="Download a mod from a gamebanana link")
    down_parser.add_argument("link", nargs="*",
            help="Mod page or download url (taken from browser)")
    down_parser.set_defaults(func=download)

    sync_parser = subparsers.add_parser("sync",
            help="Sync local mods with game directory")
    sync_parser.add_argument("-f", "--force", action="store_true",
            help="Completley wipe the in-game mods directory and sync")
    sync_parser.set_defaults(func=sync)

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_usage()

    return args


def main():
    util.configure_logging()

    util.create_dir(CONF_DIR)
    util.create_dir(MODS_DIR)
    util.create_dir(DOWNLOAD_DIR)
    util.create_dir(GAME_MOD_DIR)

    args = parse_args()
    if "func" in vars(args).keys():
        args.func(args)


if __name__ == "__main__":
    main()
