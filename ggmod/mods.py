from ggmod import util
from ggmod.const import GB_INFO_URL, CHAR_IDS
from ggmod.settings import CACHE_DIR, MODS_DIR, DOWNLOAD_DIR, MODULE_DIR
from ggmod.errors import MeshNotFoundError

from typing import Dict, Any, Optional, Union, List

from PyPAKParser import PakParser as PP

import logging
import shutil
import os
import bs4
import json



class ModDB:
    """
    Manage moddb.json stored mods - the stored JSON is a list of
    JSON objects that can be restored to fully functional Mod()
    python objects
    """
    def __init__(self):
        self.path = os.path.join(CACHE_DIR, "mod_db.json")
        
        if not os.path.exists(self.path):
            with open(path, "w") as fp:
                json.dumps([], fp)

        self._file_ro = open(self.path, "r")
        self._db = json.load(self._file_ro)

    def store_mod(self, mod: Mod) -> None:
        """
        Stores a mod as an object in a JSON file

        :param mod: the mod to store in the file
        """
        mod_data = mod._convert_to_dict()
        new_db = self._db.copy().append(mod_data)

        with open(self.path, "w") as fp:
            json.dump(new_db, fp)

    def get_mods(self) -> List[Mod]:
        """
        Returns all mods stored as objects in the JSON file

        :returns: list of stored Mod objects
        """
        mods = [Mod(**data) for data in self._db]
        return mods

    def clear(self) -> None:
        """
        Clears all mods in mod_db.json
        """
        with open(self.path, "w") as fp:
            json.dump([], fp)


class Mod:
    """
    Mod class for future compatibility and updates
    """
    def __init__(self, name: str, info: Dict[str, Any], pakfile: str, sigfile: str,
                 is_mesh=None: Optional[bool], slot=None: Optional[int], char_id=None: Optional[str],
                 _staged=None: Optional[bool]):
        self.name = name
        self.filename = info["_sFile"]
        self.description = info["_sDescription"]
        self.ts_date_added = info["_tsDateAdded"]
        self.pakfile = pakfile
        self.sigfile = sigfile

        self.stored_dir = os.path.abspath(os.path.pardir(pakfile))

        if _staged is not None:
            self.staged = _staged
        else:
            self.staged = False

        self._pp = PP(open(pakfile, "rb"))
        self._assets = map(lambda asset: pp.Unpack(asset), self._pp.List())

        self.char_id = char_id if char_id is not None else self.determine_char_id()
        self.mesh = is_mesh if is_mesh is not None else self.determine_meshed_mod()
        self.slot = slot if not mesh else self.determine_slot()

    @property
    def char_id(self):
        return self.char_id

    @property
    def mesh(self):
        return self.mesh

    @property
    def slot(self):
        return slot

    @char_id.setter
    def char_id(self, value):
        if len(char_id) != 3 and char_id not in set(CHAR_IDS.keys()):
            e = f"Character ID '{char_id}' - is invalid"
            raise ValueError(e)
        else:
            self.char_id = char_id.upper()

    @mesh.setter
    def mesh(self, value: bool)
        if value == slot:
            e = "Conflicting non-exclusive mesh and slot values "
            raise ValueError(e)
        else:
            self.mesh = value
    
    @slot.setter
    def slot(self, value: str | int | False):
        if not self.mesh and not value:
            e = "Conflicting non-exclusive mesh and slot values "
            raise ValueError(e)

        if isinstance(slot, int):
            slot = f"{slot:02d}"
        else:
            slot = value

        self.slot = slot

    def determine_meshed_mod(self):
        """
        Guess if the mod is a mesh mod

        :returns: True if any of the directories for the assets contain the word "Mesh"
        """
        return any(map(lambda asset: "Mesh" in asset.fileName, self._assets))

    def determine_char_id(self):
        """
        Rank popularity of character code sequences and choose the most popular,
        assuming the most popular character code is the correct one

        :returns: three-letter character code
        """
        char_id_search = map(lambda asset: re.search("Chara/([A-Z]{3})".encode(), asset.Data))
        matches = []

        for search_groups in char_id_search:
            if search_groups is not None:
                try:
                    matches.append(search_groups.groups(0).decode("utf-8"))
                except IndexError as e:
                    raise CharNotFoundError from e

        if not matches:
            raise CharNotFoundError("No matching character string in pak file")
        else:
            # return mode of the matches list (most common)
            return max(matches, key=matches.count)

    def determine_slot(self):
        """
        Guesswork at which slot the colour mod applies to, being such
        it only works for non-mesh mods

        :returns: either a string matching the slot code or False if the mod is mesh mod
        """
        slt_match_bytes = f"{self.char_id}/Costume[0-9]+/Material/Color([0-9]+)".encode()
        slot_search = map(lambda asset: re.search(slt_match_bytes, asset.Data))
        matches = []

        for search_groups in char_id_search:
            if search_groups is not None:
                try:
                    matches.append(search_groups.groups(0).decode("utf-8"))
                except IndexError as e:
                    raise CharNotFoundError from e

        if not matches and not self.mesh:
            raise SlotNotFoundError("No matching character string in pak file")
        else:
            # return mode of the matches list (most common)
            return max(matches, key=matches.count)

        return False if self.mesh else slot

    def override_props(self, is_mesh: bool, char_id: str, slot: int | str | False) -> None:
        """
        Override the properties if they are not detected properly. It's important
        to call this method BEFORE staging otherwise the mod will be categorised
        incorrectly

        :param is_mesh: is a mesh mod - mutually exclusive with colour mods
        :param char_id: three-letter character identification code
        :param slot: the slot of which the colour mod applies to
        """
        self.mesh = is_mesh
        self.char_id = char_id
        self.slot = slot

    def stage(self) -> None:
        """
        Place downloaded mod into the staging folder which will be copied
        from when ggmod.sync is called
        """
        stored_dir = os.path.join(MODS_DIR, self.name)

        pakfile = self.pakfile.strip(os.sep).split(os.sep)[-1]
        sigfile = self.sigfile.strip(os.sep).split(os.sep)[-1]

        shutil.copy(pakfile, stored_dir)
        shutil.copy(sigfile, stored_dir)

        self.stored_dir = stored_dir
        self.staged = True

    def unstage(self):
        """
        Remove mod from staging folder
        """
        if not self.staged:
            e = f"Cannot unstage a mod that is not staged"
            raise ValueError(e)

        pakfile = self.pakfile.strip(os.sep).split(os.sep)[-1]
        sigfile = self.sigfile.strip(os.sep).split(os.sep)[-1]

        os.remove(os.path.join(self.stored_dir, pakfile))
        os.remove(os.path.join(self.stored_dir, sigfile))

    def _convert_to_dict(self) -> str:
        """
        Convert to json text form to be put into a .json file
        and given as kwargs to __init__ upon loading from said
        file

        :returns: Valid JSON string of all class attributes
        """

        self_data = {}
        self_data["name"] = self.name
        self_data["info"] = {
            "_sFile": self.filename,
            "_sDescription": self.description,
            "_tsDateAdded": self.ts_date_added
        }
        self_data["pakfile"] = self.pakfile
        self_data["sigfile"] = self.sigfile
        self_data["mesh"] = self.mesh
        self_data["slot"] = self.slot
        self_data["char_id"] = self.char_id
        self_data["staged"] = self.staged
        return self_data


class ModLink:
    """
    Intermediary class between ModPage and Mod
    """
    def __init__(self, name: str, info: Dict):
        self.name = name
        self._info = info
        self.filename = info["_sFile"]
        self.description = info["_sDescription"]
        self.ts_date_added = info["_tsDateAdded"]

        self._download_url = info["_sDownloadUrl"]
        self._download_path = os.path.join(DOWNLOAD_DIR, self.filename)

    def download(self) -> Mod:
        """
        This is just to get the archives and extract them in a reasonable location
        """
        if os.path.exists(self._download_path):
            logging.debug(f"Already downloaded mod at {self._download_path}")
        else:
            logging.debug(f"Downloading shiny new mod archive {self._download_path}")

            response = util.get_request(self._download_url)
            with open(self._download_path, "wb") as fp:
                fp.write(response.content)

        decomp_paths = util.decompress(self._download_path, self.name)

        pakfile = filter(lambda p: p.endswith(".pak"), decomp_paths)
        sigfile = filter(lambda p: p.endswith(".sig"), decomp_paths)

        if not sigfile:
            original_sigfile = os.path.join(MODULE_DIR, "sigfile.sig")
            sigfile = pakfile.replace(".pak", ".sig")
            shutil.copy(original_sigfile,  sigfile)

        if not pakfile:
            e = f"No pakfile (.pak) found in archive {self.filename}"
            raise FileNotFoundError(e)

        return Mod(name, self._info, pakfile, sigfile)


class ModPage:
    """
    Mods and mod metadata extracted from gamebanana webpages
    """
    def __init__(self, url: str):
        info_response = util.get_request(GB_INFO_URL.format(url.split("/")[-1]))
        page_response = util.get_request(url)

        webpage = bs4.BeautifulSoup(page_response.content)
        title_tag = webpage.find(lambda tag: tag.get("id") == "PageTitle")

        self.name = list(title_tag.children)[0].strip().lower()
        self.name = self.name.replace(" ", "-").replace("'", "")

        self.__files_data = info_response.json()["_aFiles"]
        self.__mods = [ModLink(self.name, info) for info in self.__files_data]

    def __iter__(self) -> Dict:
        yield from self._mods

    def __len__(self) -> int:
        return len(self._mods)

    def __getitem__(self, key) -> ModLink:
        return self.__mods[key]
