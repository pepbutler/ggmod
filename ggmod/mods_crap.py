from ggmod import util
from ggmod.const import GB_INFO_URL, CHAR_IDS
from ggmod.settings import MODS_DIR, DOWNLOAD_DIR, MODULE_DIR

from typing import Dict

from PyPAKParser import PakParser as PP

import logging
import shutil
import re
import os


class Mod:
    def __init__(self, info: Dict, is_mesh=None, char_id=None, slot=None):
        self.filename = info["_sFile"]
        self.description = info["_sDescription"]
        self.ts_date_added = info["_tsDateAdded"]

        self.__download_url = info["_sDownloadUrl"]
        self.__is_mesh = is_mesh
        self.__char_id = char_id
        self.__slot = slot
        self.__dest_path = None

        self.loaded = False
        self.__load_from_cache()

    def is_mesh(self) -> bool:
        if not self.loaded:
            e = "Mod has not been downloaded yet, information not available"
            raise ValueError(e)
        else:
            return self.__is_mesh

    def get_char_id(self) -> str:
        if not self.loaded:
            e = "Mod has not been downloaded yet, information not available"
            raise ValueError(e)
        else:
            return self.__char_id

    def get_slot(self) -> str:
        if not self.loaded:
            e = "Mod has not been downloaded yet, information not available"
            raise ValueError(e)
        else:
            return self.__slot

    def download(self) -> str | bytes:
        logging.debug("Mod download started")
        dl_mod_file = os.path.join(DOWNLOAD_DIR, self.filename)

        if not self.loaded:
            if self.__download_url.startswith("unverum"):
                self.__download_url = util.convert_toolurl(self.__download_url)

            if os.path.exists(dl_mod_file):
                print(f"[*] Using cached downloads/{dl_mod_file}")
            else:
                print(f"[*] Downloading {dl_mod_file} from {self.__download_url}")
                dl_response = util.get_request(self.__download_url)

                print(f"[*] Writing {dl_mod_file}")
                with open(dl_mod_file, "wb") as fp:
                    fp.write(dl_response.content)

                print(f"[!] Downloaded {dl_mod_file}")

        logging.debug("Mod download finished")

        self.__decompress(dl_mod_file)

        return dl_mod_file

    def __load_from_cache(self):
        """If cached, automatically load"""
        dl_mod_file = os.path.join(DOWNLOAD_DIR, self.filename)
        if os.path.exists(dl_mod_file):
            self.download()

    def select(self, files):
        if os.listdir(self.__dest_path):
            print(f"[!] Mod found at {self.__dest_path} slot for {CHAR_IDS[self.get_char_id()]}")
            do_replace = util.input_yn("[?] Replace existing mod? (Y/n) -> ")

            if do_replace:
                *_, marked_files = next(os.walk(self.__dest_path))
                print(f"[!] Removing {len(marked_files)} files!")
                for marked_file in marked_files:
                    os.remove(os.path.join(self.__dest_path, marked_file))
            else:
                if self.is_mesh():
                    # multiple mesh mods can sometimes be used
                    do_add = util.input_yn("Add mod instead? (Y/n) -> ")
                    if do_add:
                        print("[*] Adding mod")
                        pass
                    else:
                        print("[!] Cancelling mod download!")
                        return
                else:
                    print("[!] Cancelling mod download!")
                    return

        for file in files:
            shutil.copy(file, self.__dest_path)

    def __get_mod_info(self, path):
        is_mesh_mod = False

        with open(path, "rb") as pakfile:
            pp = PP(pakfile)
            mod_assets = pp.List()

            base_asset = ""
            char_name = ""
            char_id = ""
            slot = ""

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
                    slot = match[len(match) - 2:]
                    print(f"[?] Texture slot seems to be {slot}")
            else:
                slot = f"{slot:02d}"


        mod_type = "Mesh" if is_mesh_mod else "Texture"
        print(f"[*] {mod_type}{slot} mod for {char_name}")

        self.__is_mesh = is_mesh_mod
        self.__char_id = char_id
        self.__slot = slot

        directory = "mesh" if self.is_mesh() else self.get_slot()
        chosen_dir = os.path.join(MODS_DIR, self.get_char_id(), directory)
        util.create_dir(chosen_dir)

        self.__dest_path = chosen_dir
        self.loaded = True

    def __decompress(self, filename: str | bytes):
        # this causes everything to happen in this branch of code
        if filename.endswith("rar") or filename.endswith("zip") or filename.endswith("7z"):
            os.system(f"7z e {filename} -o{DOWNLOAD_DIR} >/dev/null")
        else:
            e = "Unknown archive format from file {}".format(filename)
            raise ValueError(e)

        sigfile = pakfile = None
        *_, local_files = next(os.walk(DOWNLOAD_DIR))

        for file in local_files:
            if file.endswith("pak"):
                pakfile = os.path.join(DOWNLOAD_DIR, file)
            elif file.endswith("sig"):
                sigfile = os.path.join(DOWNLOAD_DIR, file)

        if pakfile is None:
            e = f"No pak file found for mod {self.filename}"
            raise FileNotFoundError(e)

        if sigfile is None:
            old_sigfile = os.path.join(MODULE_DIR, "sigfile.sig")
            sigfile = os.path.join(DOWNLOAD_DIR, pakfile.rstrip(".pak") + ".sig")

            shutil.move(old_sigfile, sigfile)

        download_path = os.path.join(MODULE_DIR, filename)
        shutil.move(filename, download_path)

        self.__get_mod_info(pakfile)
        return pakfile, sigfile


class ModPage:
    def __init__(self, url: str):
        info_response = util.get_request(GB_INFO_URL.format(url.split("/")[-1]))
        self.__files_data = info_response.json()["_aFiles"]
        self.__mods = [Mod(info) for info in self.__files_data]

    def __iter__(self) -> Dict:
        yield from self._mods

    def __len__(self):
        return len(self._mods)

    def __getitem__(self, key):
        return self.__mods[key]
