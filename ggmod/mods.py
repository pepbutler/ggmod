from ggmod import util
from ggmod.const import GB_INFO_URL, CHAR_IDS
from ggmod.settings import MODS_DIR, DOWNLOAD_DIR

from typing import Union, Dict, Optional

import re
import tempfile


class Mod:
    def __init__(self, info: Dict):
        self.filename = info["_sFile"]
        self.description = info["_sDescription"]
        self.ts_date_added = info["_tsDateAdded"]

        self.__download_url = info["_sDownloadUrl"]
        self.__is_mesh = self.__char_id = self.__slot = None

        self.loaded = False
        self.__load_from_cache()

    def is_mesh(self) -> Optional[bool]:
        if not self.loaded:
            e = "Mod has not been downloaded yet, information not available"
            raise ValueError(e)
        else:
            return self.__is_mesh

    def get_char_id(self) -> Optional[str]:
        if not self.loaded:
            e = "Mod has not been downloaded yet, information not available"
            raise ValueError(e)
        else:
            return self.__char_id

    def get_slot(self) -> Optional[str]:
        if not self.loaded:
            e = "Mod has not been downloaded yet, information not available"
            raise ValueError(e)
        else:
            return self.__slot

    def download(self) -> os.PathLike:
        if loaded:
            return

        if self.__download_url.startswith("unverum"):
            self.__download_url = util.convert_toolurl(download_url)

        dl_mod_file = os.path.join(DOWNLOAD_DIR, self.filename)

        if os.path.exists(dl_mod_file):
            print(f"[*] Using cached downloads/{mod_file}")
            return dl_mod_file
        else:
            print(f"[*] Downloading {mod_file} from {self.__download_url}")
            dl_response = util.get_request(self.__download_url)
    
            print(f"[*] Writing {mod_file}")
            with open(dl_mod_file, "wb") as f:
                f.write(dl_response.content)
    
            print(f"[!] Downloaded {mod_file}")

        self.loaded = True

        pakfile, sigfile = self.__decompress(dl_mod_file)
        self.__move_to_mods(pakfile, sigfile)


    def __load_from_cache(self):
        dl_mod_file = os.path.join(DOWNLOAD_DIR, self.filename)
        if os.path.exists(dl_mod_file):
            self.download()


    def __move_to_mods(self, *args):
        chosen_dir = self.__form_dest_path(self.is_mesh(), self.get_char_id(), self.get_slot())

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
                    # multiple mesh mods can sometimes be used
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
    
        for path in args:
            shutil.move(path, os.path.join(chosen_dir, path))


    @static
    def __form_dest_path(is_mesh, char_id, slot) -> os.PathLike:
        directory = "mesh" if is_mesh else slot
        chosen_dir = os.path.join(MOD_DIR, char_id, directory)
        util.mkdir(chosen_dir)
        return chosen_dir

    def __get_mod_info(path):
        is_mesh_mod = False

        with open(path, "rb") as pakfile:
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
    
        is_correct = util.input_yn("[?] Is this correct? (Y/n) -> ")
        if not is_correct:
            is_mesh_mod = util.input_yn("[?] Is mesh mod? (Y/n) -> ")
            if not is_mesh_mod:
                slot = int(input("Slot(number) -> "))
                slot = f"{slot:02d}"
    
        mod_type = "Mesh" if is_mesh_mod else "Texture"
        print(f"[*] {mod_type}{slot} mod for {char_name}")
    
        return is_mesh_mod, char_id, slot



    @static
    def __decompress(filename: Union[str, os.PathLike]):
        with tempfile.TemporaryDirectory(delete_on_close=False) as tempdir:
            if filename.endswith("rar") or filename.endswith("zip") or filename.endswith("7z"):
                os.system(f"7z e {filename} -o {tempdir}")
            else:
                e = "Unknown archive format from file {}".format(filename)
                raise ValueError(e)
    
            sigfile = pakfile = None
            *_, local_files = next(os.walk(MODS_DIR))
            for file in local_files:
                if file.endswith("pak"):
                    pakfile = file
                elif file.endswith("sig"):
                    sigfile = file

            if pakfile is None:
                e = f"No pak file found for mod {self.filename}"
                raise FileNotFoundError(e)
    

            if sigfile is None:
                old_sigfile = os.path.join(tempdir, "sigfile.sig")
                sigfile = os.path.join(tempdir, pakfile.rstrip(".pak") + ".sig")

                shutil.move(old_sigfile, sigfile)
    
            download_path = os.path.join(MODULE_DIR, filename)
            util.mkdir(DOWNLOAD_DIR)
            shutil.move(filename, download_path)
            self.__is_mesh, self.__char_id, self.__slot = self.__get_mod_info(tempdir)
            return pakfile, sigfile


class ModPage:
    def __init__(self, url: str):
        info_response = util.get_request(GB_INFO_URL.format(url.split("/")[-1]))
        self._files_data = info_response.json()["_aFiles"]
        self._mods = (Mod(info) for info i self._files_data,)

    def __iter__(self) -> Dict:
        yield from self._mods

    def __len__(self):
        return len(self._mods)
