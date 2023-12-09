from argparse import ArgumentParser
from PyPAKParser import PakParser as PP

import shutil
import os

HOME_DIR = os.getenv("HOME")
MODS_DIR = f"{HOME_DIR}/.steam/debian-installation/steamapps/common/GUILTY GEAR STRIVE/RED/Content/Paks/~mods"

BASE_DIR = os.path.join(os.curdir, "mods")
DOWNLOAD_DIR = os.path.join(os.curdir, "downloads")

GB_DOWNLOAD_LINK = "https://files.gamebanana.com/mods"
GB_INFO_LINK = "https://gamebanana.com/apiv10/Mod/{}/DownloadPage"

CHAR_IDS = {
    "ASK": "Asuka R#",
    "SOL": "Sol Badguy",
    "KYK": "Ky Kiske",
    "MAY": "May",
    "AXL": "Axl Low",
    "CHP": "Chipp Zanuff",
    "POT": "Potemkin",
    "FAU": "Faust",
    "MLL": "Millia Rage",
    "ZAT": "Zato-1",
    "RAM": "Ramlethal",
    "LEO": "Leo Whitefang",
    "NAG": "Nagoryuki",
    "GIO": "Giovanna",
    "ANJ": "Anji Mito",
    "INO": "I-No",
    "GLD": "Goldlewis",
    "JKO": "Jack-O",
    "COS": "Happy Chaos",
    "BKN": "Baiken",
    "TST": "Testament",
    "SIN": "Sin Kiske",
    "BGT": "Bridget",
    "ELP": "Elphelt", 
}


def yn_choice(prompt):
    return input(prompt).lower().startswith("y")


def mkdir_if_missing(path):
    if not os.path.exists(path):
        os.makedirs(path)


def download_mod(mod_id):
    import requests

    inf_response = requests.get(GB_INFO_LINK.format(mod_id))
    print(f"[* <{inf_response.status_code}>] Requesting mod info for {mod_id}")

    info = inf_response.json()
    files = info["_aFiles"]

    if len(files) == 1:
        mod_file = files[0]["_sFile"]
        download_url = files[0]["_sDownloadUrl"]
    else:
        for i, file in enumerate(files):
            mod_file = file["_sFile"]
            mod_desc = file["_sDescription"]
            print(f"[{i + 1}] {mod_file} - {mod_desc}")

        choice = int(input("Choice no. -> ")) - 1
        download_url = files[choice]["_sDownloadUrl"]
        mod_file = files[choice]["_sFile"]

    if download_url.startswith("unverum"):
        download_url = download_url.replace("unverum:", "").replace("mmdl", "dl").split(",")[0]

    dl_mod_file = os.path.join(DOWNLOAD_DIR, mod_file)
    if os.path.exists(dl_mod_file):
        print(f"[*] Using cached downloads/{mod_file}")
        os.rename(dl_mod_file, mod_file)
    else:
        print(f"[*] Downloading {mod_file} {download_url}")
        dl_response = requests.get(download_url)

        print(f"[*] Writing {mod_file}")
        with open(mod_file, "wb") as f:
            f.write(dl_response.content)

        print(f"[!] Downloaded {mod_file}")

    return mod_file


def decompress_mod(fn: str):
    # this may cause problems
    if fn.endswith("rar") or fn.endswith("zip") or fn.endswith("7z"):
        os.system(f"7z e {fn}")

    sigfile = None
    *_, local_files = next(os.walk(os.curdir))
    for file in local_files:
        if file.endswith("pak"):
            pakfile = file
        elif file.endswith("sig"):
            sigfile = file

    if sigfile is None:
        old_sigfile = os.path.join(os.curdir, "sigfile.sig")
        sigfile = os.path.join(os.curdir, pakfile.rstrip(".pak") + ".sig")
        os.rename(old_sigfile, sigfile)

    download_path = os.path.join(DOWNLOAD_DIR, fn)
    print(download_path)
    mkdir_if_missing(DOWNLOAD_DIR)
    os.rename(fn, download_path)
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

    is_correct = yn_choice("[?] Is this correct? (Y/n) -> ")
    if not is_correct:
        is_mesh_mod = yn_choice("Is mesh mod? (Y/n) -> ")
        if not is_mesh_mod:
            slot = int(input("Slot(number) -> "))
            slot = f"{slot:02d}"

    mod_type = "Mesh" if is_mesh_mod else "Texture"
    print(f"[*] {mod_type}{slot} mod for {char_name}")

    return is_mesh_mod, char_id, slot


def place_mod(char_id, pak_fn, sig_fn, is_mesh, slot):
    dir_append = "mesh" if is_mesh else slot
    chosen_dir = os.path.join(BASE_DIR, char_id, dir_append)
    mkdir_if_missing(chosen_dir)

    if os.listdir(chosen_dir):
        print(f"[!] Mod found at {dir_append} slot for {CHAR_IDS[char_id]}")
        do_replace = yn_choice("Replace existing mod? (Y/n) -> ")

        if do_replace:
            *_, marked_files = next(os.walk(chosen_dir))
            print(f"[!] Removing {len(marked_files)} files!")
            for marked_file in marked_files:
                os.remove(os.path.join(chosen_dir, marked_file))
        else:
            if is_mesh:
                do_add = yn_choice("Add mod instead? (Y/n) -> ")
                if do_add:
                    print("[*] Adding mod")
                    pass
                else:
                    print("[!] Cancelling mod download!")
                    return
            else:
                print("[!] Cancelling mod download!")
                return

    os.rename(pak_fn, os.path.join(chosen_dir, pak_fn))
    os.rename(sig_fn, os.path.join(chosen_dir, sig_fn))


def download(mod_id):
    mod_fn = download_mod(mod_id)
    pak_fn, sig_fn = decompress_mod(mod_fn)
    is_mesh_mod, char_id, slot = get_mod_info(pak_fn)

    place_mod(char_id, pak_fn, sig_fn, is_mesh_mod, slot)


def sync():
    mkdir_if_missing(MODS_DIR)

    all_files = []
    all_flat_files = []
    for root, _, files in os.walk(BASE_DIR):
        all_flat_files += files
        all_files += list(map(lambda f: os.path.join(root, f), files))

    *_, active_mods = next(os.walk(MODS_DIR))
    for mod in active_mods:
        os.remove(os.path.join(MODS_DIR, mod))
        print(f"[!] Removing {os.path.join(MODS_DIR, mod)}")

    for path, flat_path in zip(all_files, all_flat_files):
        # the only time shutil is used
        try:
            shutil.copy(path, os.path.join(MODS_DIR, flat_path))
        except BaseException as e:
            print(e, path, os.path.join(MODS_DIR, flat_path))
            exit()
        print(f"[*] Copying {path} to {os.path.join(MODS_DIR, flat_path)}")


# $ ggmod download <link>
#   ggmod remove <mod>
#   ggmod list jacko
#   ggmod use jacko skin <mod>
#   ggmod use jacko mesh <mod>
#   ggmod list nago 1 (slot 1)
#   ggmod rename <old> <new>


def main():
    parser = ArgumentParser()
    parser.add_argument("download", nargs="*")
    parser.add_argument("remove", nargs="*")
    parser.add_argument("sync", nargs="*")
    parser.add_argument("list", nargs="*")
    parser.add_argument("rename", nargs="*")
    parser.add_argument("use", nargs="*")
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.error("Must specify an argument such as 'download' or 'list'")

    # WARNING: i broke argparse somehow??
    if args.download:
        actual_arg, *args = args.download
        if actual_arg == "download":
            if len(args) > 1:
                print("[!] Installing multiple mods")
                for arg in args:
                    download(arg.split("/")[-1])
            else:
                download(args[0].split("/")[-1])
        elif actual_arg == "sync":
            sync()


if __name__ == "__main__":
    main()
