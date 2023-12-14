from ggmod import util
from ggmod.const import GB_INFO_URL, CHAR_IDS
from ggmod.settings import MODS_DIR, DOWNLOAD_DIR, MODULE_DIR

from typing import Dict, Any, Optional, Union

from PyPAKParser import PakParser as PP

import logging
import shutil
import re
import os


class Mod:
    """
    Mod class for future compatibility and updates
    """
    def __init__(self, info: Dict[str, Any], pakfile: str, sigfile: str,
            is_mesh=None: Optional[bool], slot=None: Optional[int], char_id=None: Optional[str]):
        self.filename = info["_sFile"]
        self.description = info["_sDescription"]
        self.ts_date_added = info["_tsDateAdded"]
        self.pakfile = pakfile
        self.sigfile = sigfile

        self.mesh = is_mesh if is_mesh is not None else self.determine_meshed_mod()
        self.char_id = char_id if char_id is not None else self.determine_char_id()
        self.slot = slot if not mesh else self.determine_slot()

    def determine_char_id(self)
        return None

    def determine_char_id(self):
        return None

    def determine_slot(self):
        return None

    def stage(self):
        shutil.copy(self.pakfile, os.path.join(MODS_DIR))
        shutil.copy(self.sigfile, os.path.join(MODS_DIR))


class ModLink:
    """
    Intermediary class between ModPage and actual mod
    """
    def __init__(self, info: Dict):
        self._info = info
        self.filename = info["_sFile"]
        self.description = info["_sDescription"]
        self.ts_date_added = info["_tsDateAdded"]

        self._download_url = info["_sDownloadUrl"]
        self._destined_path = os.path.join(DOWNLOAD_DIR, self.filename)

    def download(self) -> Mod:
        """This is just to get the archives and extract them in a decent location"""
        if os.path.exists(self._destined_path):
            logging.debug("Already downloaded mod at {self._destined_path}")
        else:
            logging.debug("Downloading shiny new mod archive {self._destined_path}")

            response = util.get_request(self._download_url)
            with open(self._destined_path, "wb") as fp:
                fp.write(response.content)

        decomp_paths = util.decompress(self._destined_path, self.filename.split(".")[0])

        pakfile = filter(lambda p: p.endswith(".pak"), decomp_paths)
        sigfile = filter(lambda p: p.endswith(".sig"), decomp_paths)

        if not sigfile:
            original_sigfile = os.path.join(MODULE_DIR, "sigfile.sig")
            sigfile = pakfile.replace(".pak", ".sig")
            shutil.copy(original_sigfile,  sigfile)

        return Mod(self._info, pakfile, sigfile)


class ModPage:
    """
    Mods and mod metadata extracted from gamebanana webpages
    """
    def __init__(self, url: str):
        info_response = util.get_request(GB_INFO_URL.format(url.split("/")[-1]))
        self.__files_data = info_response.json()["_aFiles"]
        self.__mods = [ModLink(info) for info in self.__files_data]

    def __iter__(self) -> Dict:
        yield from self._mods

    def __len__(self) -> int:
        return len(self._mods)

    def __getitem__(self, key) -> ModLink:
        return self.__mods[key]
