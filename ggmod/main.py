from argparse import ArgumentParser

from ggmod import util
from ggmod.settings import MODS_DIR, DOWNLOAD_DIR, GAME_MOD_DIR, CONF_DIR
from ggmod.mods import ModPage, ModDB

import shutil
import os

import string


def download(args):
    print(f"[*] Processing {len(args.link)} mods from GB...")
    modpage = ModPage(args.link)

    if len(modpage) > 1:
        for i, modlink in enumerate(modpage):
            print(f"[{i+1}] {modlink.name} - {modlink.description}")

        choice = input("[?] Choice: ")
        if not all(char in string.digits for char in choice):
            choice = None
        else:
            choice = int(choice) - 1
    elif len(modpage) == 1:
        modlink = modpage[0]
        print(f"[*] Selected mod: {modlink.name} - {modlink.description}")
        choice = 0 if util.input_yn("[?] Stage this archive (Y/n) ") else None

    if choice or choice is not None:
        print("[*] Staging mod...")

        chosen_mod = modpage[choice].download()
        if hasattr(args, "slot"):
            chosen_mod.override_props()
        chosen_mod.stage()

        mod_db = ModDB()
        mod_db.store_mod(chosen_mod)

        print("[!] Done")
    else:
        print("[!] иди на хуй :D")
        exit(0)


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
        - User can download a mod from a webpage, should
          grant user freedom of choice and be robust
        - Assigns a name to the new mod

    ggmod remove <mod name>
        - Delete mod files from staging folder, KEEP archive

    ggmod clean
        - Remove ALL archives in cache folder

    ggmod list JKO
        - Tabulated list of active and inactive mesh and
          colour mods

    ggmod use JKO col8 <mod name>
        - Use a certain colour mod

    ggmod use JKO mesh <mod name>
        - Self-explanatory

    ggmod rename <old name> <new name>
        - Rename mod

    ggmod sync
        - Synchronise mod changes across staging folderand
          and actual game dir
    """

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help="List of subcommands")

    down_parser = subparsers.add_parser(
        "download", help="Download a mod from gamebanana link"
    )
    down_parser.add_argument("link", help="Gamebanana mod page URL")
    down_parser.add_argument(
        "-s", "--slot", type=int, help="Specify the slot the color mod applies to"
    )
    down_parser.add_argument(
        "-m", "--mesh", type=bool, help="Specify as mesh mod (mutal exclusive w/ slot)"
    )
    down_parser.set_defaults(func=download)

    sync_parser = subparsers.add_parser(
        "sync", help="Sync all local mods with game directory"
    )
    sync_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Completly wipe the in-game mods directory and sync",
    )
    sync_parser.set_defaults(func=sync)

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_usage()
    else:
        if hasattr(args, "slot") and hasattr(args, "mesh"):
            if args.slot and args.mesh:
                parser.error("Cannot have both slot and mesh mod (use one!)")

    return args


def main():
    util.configure_logging()

    util.create_dir(CONF_DIR)
    util.create_dir(MODS_DIR)
    util.create_dir(DOWNLOAD_DIR)
    util.create_dir(GAME_MOD_DIR)

    args = parse_args()

    # whenever not using subcommands e.g. --help
    if "func" in vars(args).keys():
        args.func(args)


if __name__ == "__main__":
    main()
