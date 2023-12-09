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



class Mod:
    def __init__(self, info: Dict):
        self.filename = info


def input_yn(prompt, *args):
    return input(prompt.format(*args)).lower().startswith("y")


def choose_mod_dl(modpage_url)
    info_response = requests.get(GB_INFO_URL.format(mod_id))
    logging.debug(f"<{info_response.status_code}> {info_response.text[:50]}")

    if info_response.status_code > 399:
        logging.warning(f"<{info_response.status_code}> {info_response.text}"

    print(f"[*] Requesting mod info for {mod_id}")

    info = info_response.json()
    mods = info["_aFiles"]

    mods_info = map(lambda i: i["_sFile"], i["_sDescription"], i["_sDownloadUrl"], mods)

    if len(mods_info) > 1:
        for i, info in enumerate(mods_info):
            print(f"[{i + 1}] {info[0]}: {info[1]}")

        choice = input("Choice no. -> ")
        if not choice.match("[0-9]+", choice):
            e = "Invalid choice of mod '{}'".format(choice)
            raise ValueError(e)
        else:
            choice = int(choice) - 1
    else:
        choice = 0
        info = mods_info[choice]
        print(f"[*] Target: {info[0]} by {info[1]}")

    return mods_info[choice][0:-1]



def download_mod(download_url, filename):
    if download_url.startswith("unverum"):
        download_url = download_url.replace("unverum:", "").replace("mmdl", "dl").split(",")[0]

    dl_mod_file = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(dl_mod_file):
        print(f"[*] Using cached downloads/{mod_file}")
        return dl_mod_file
    else:
        print(f"[*] Downloading {mod_file} from {download_url}")
        dl_response = requests.get(download_url)

        print(f"[*] Writing {mod_file}")
        with open(dl_mod_file, "wb") as f:
            f.write(dl_response.content)

        print(f"[!] Downloaded {mod_file}")

    return dl_mod_file


def decompress_mod(filename: str):
    if filename.endswith("rar") or filename.endswith("zip") or filename.endswith("7z"):
        os.system(f"7z e {filename} -o {MOD_DIR}")
    else:
        e = "Unknown archive format from file {}".format(filename)
        raise ValueError(e)

    sigfile = pakfile = None
    *_, local_files = next(os.walk(os.curdir))
    for file in local_files:
        if file.endswith("pak"):
            pakfile = file
        elif file.endswith("sig"):
            sigfile = file

    if sigfile is None:
        old_sigfile = os.path.join(os.curdir, "sigfile.sig")
        sigfile = os.path.join(os.curdir, pakfile.rstrip(".pak") + ".sig")
        shutil.move(old_sigfile, sigfile)

    download_path = os.path.join(DOWNLOAD_DIR, filename)
    print(download_path)
    util.mkdir(DOWNLOAD_DIR)
    shutil.move(filename, download_path)
    return pakfile, sigfile


# this needs improving sometime
def get_mod_info(fn):
    import re
    is_mesh_mod = False
    with open(fn, "rb") as pakfile:
        pp = PP(pakfile)
        mod_assets = pp.List()
        base_asset = ""
        char_name = ""
        char_id = ""
        for asset in mod_assets:
            for id, name in CHAR_IDS.items():
                data = str(pp.Unpack(asset).Data)
                # this is very dodgy
                if f"Chara/{id}" in data and not char_id:
                    print(f"[?] Detected {name} character pattern in {asset}")
                    char_id = id
                    char_name = name

                # so is this
                if not is_mesh_mod:
                    is_mesh_mod = "Mesh" in data and "shader" not in asset
                    if is_mesh_mod:
                        print(f"[?] Detected mesh pattern in {asset}")

            match_base = re.search(".*[A-Z]{3}_base.uasset", asset)
            if match_base is not None:
                base_asset = asset

        if not is_mesh_mod:
            if not base_asset:
                # base_asset = f"{char_id}_base.uasset"
                base_asset = list(mod_assets)[0]
            data = pp.Unpack(base_asset).Data
            match = re.search("Color[0-9]+", str(data))
            if match is not None:
                match = match.group(0)
                slot = match[len(match)-2:]
                print(f"[?] Texture slot seems to be {slot}")
        else:
            slot = ""

    is_correct = input_yn("[?] Is this correct? (Y/n) -> ")
    if not is_correct:
        is_mesh_mod = input_yn("[?] Is mesh mod? (Y/n) -> ")
        if not is_mesh_mod:
            slot = int(input("Slot(number) -> "))
            slot = f"{slot:02d}"

    mod_type = "Mesh" if is_mesh_mod else "Texture"
    print(f"[*] {mod_type}{slot} mod for {char_name}")

    return is_mesh_mod, char_id, slot


def place_mod(char_id, pak_fn, sig_fn, is_mesh, slot):
    dir_append = "mesh" if is_mesh else slot
    chosen_dir = os.path.join(BASE_DIR, char_id, dir_append)
    util.mkdir(chosen_dir)

    if os.listdir(chosen_dir):
        print(f"[!] Mod found at {dir_append} slot for {CHAR_IDS[char_id]}")
        do_replace = input_yn("[?] Replace existing mod? (Y/n) -> ")

        if do_replace:
            *_, marked_files = next(os.walk(chosen_dir))
            print(f"[!] Removing {len(marked_files)} files!")
            for marked_file in marked_files:
                os.remove(os.path.join(chosen_dir, marked_file))
        else:
            if is_mesh:
                do_add = input_yn("Add mod instead? (Y/n) -> ")
                if do_add:
                    print("[*] Adding mod")
                    pass
                else:
                    print("[!] Cancelling mod download!")
                    return
            else:
                print("[!] Cancelling mod download!")
                return

    shutil.move(pak_fn, os.path.join(chosen_dir, pak_fn))
    shutil.move(sig_fn, os.path.join(chosen_dir, sig_fn))


def download(mod_urls):
    import requests

    for url in mod_urls:
        if not re.match(MODPAGE_URL_RE, url):
            e = "Invalid download link '{}' provided".format(download_mod)
            raise ValueError(e)
        else:
            logging.debug(f"{url} matches {MODPAGE_URL_RE}")

        download_link, filename = choose_mod_dl(url)

        download_mod(download_link, filename)
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
