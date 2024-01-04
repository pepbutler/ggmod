from ggmod import util
from ggmod.const import GB_INFO_URL, CHAR_IDS
from ggmod.settings import CACHE_DIR, MODS_DIR, DOWNLOAD_DIR, MODULE_DIR
from ggmod.errors import SlotNotFoundError, CharNotFoundError

from typing import Dict, Generator, Optional, List

from PyPAKParser import PakParser as PP

from statistics import mode

import logging
import shutil
import os
import bs4
import json
import re

from typing import Union


class Mod:
    """
    Represents an individual mod, i.e. an Unreal Engine 4 .pak file that contains an
    alternative mesh or color slot alteration

    Mod objects must have a name used for organising and referring to them in storage,
    as well as metadata from gamebanana and from the user. If not provided then determine
    the latter automatically. The staging method allows the user to correct the generated
    properties beforehand.
    """

    def __init__(
        self,
        name: str,
        info: Dict[str, Union[str, bool, int]],
        pakfile: str,
        sigfile: str,
        is_mesh: Optional[bool] = None,
        slot: Optional[int] = None,
        char_id: Optional[str] = None,
        _staged: Optional[bool] = None,
    ):
        """
        Create a new mod object with provided metadata and properties

        :param name: Shortened or colloquialised name of the mod
        :param info: Metadata stipped from gamebanana website
        """
        self.name = name
        self.filename = info["_sFile"]
        self.description = info["_sDescription"]
        self.ts_date_added = info["_tsDateAdded"]
        self.pakfile = pakfile
        self.sigfile = sigfile

        self.stored_dir = os.path.abspath(os.path.join(pakfile, os.pardir))

        if _staged is not None:
            self.staged = _staged
        else:
            self.staged = False

        self._pp = PP(open(pakfile, "rb"))
        self._asset_paths = self._pp.List()
        self._assets = [self._pp.Unpack(path) for path in self._asset_paths]

        self._char_id = char_id
        self._mesh = is_mesh
        if not is_mesh:
            self._slot = slot
        else:
            raise ValueError("Cannot specify mod as mesh and colour slot mod")

    def determine_props(self):
        """
        Hopefully a temporary method
        """
        self._char_id = (
            self.char_id if self.char_id is not None else self.determine_char_id()
        )

        self._mesh = (
            self.is_mesh if self.is_mesh is not None else self.determine_meshed_mod()
        )

        if not self._mesh:
            self._slot = self.slot if self.slot is not None else self.determine_slot()
        else:
            self._slot = None

    @property
    def char_id(self):
        return self._char_id

    @char_id.setter
    def char_id(self, value):
        if len(value) != 3 and value not in set(CHAR_IDS.keys()):
            e = f"Character ID '{value}' - is invalid"
            raise ValueError(e)
        else:
            self._char_id = value.upper()

    @property
    def mesh(self):
        return self._mesh

    @mesh.setter
    def mesh(self, value: bool):
        self._mesh = value

    @property
    def slot(self):
        return self._slot

    @slot.setter
    def slot(self, value: str | int):
        if bool(self._mesh) == bool(value):
            e = "Conflicting non-exclusive mesh and slot values "
            raise ValueError(e)

        if isinstance(value, int):
            slot = f"{value:02d}"
        else:
            slot = value

        self._slot = slot

    def determine_meshed_mod(self):
        """
        Guess if the mod is a mesh mod

        :returns: True if any of the directories for the assets contain the word "Mesh"
        """
        return any(map(lambda path: "mesh" in path.lower(), self._asset_paths))

    def determine_char_id(self):
        """
        Rank popularity of character code sequences and choose the most popular,
        assuming the most popular character code is the correct one

        :returns: three-letter character code
        """
        char_id_search = list(
            map(
                lambda asset: re.search("Chara/([A-Z]{3})".encode(), asset.Data),
                self._assets,
            )
        )
        matches = []

        for search_groups in list(char_id_search):
            if search_groups is not None:
                try:
                    matches.append(search_groups.groups(0)[0].decode("utf-8"))
                except IndexError as e:
                    raise CharNotFoundError from e

        if not matches or matches == []:
            e = "No matching character string in pak file"
            raise CharNotFoundError(e)
        else:
            # return mode of the matches list (most common)
            return max(matches, key=matches.count)

    def determine_slot(self):
        """
        Guesswork at which slot the colour mod applies to, being such
        it only works for non-mesh mods

        This function sometimes never guesses the slot correctly

        :returns: either a string matching the slot code or False if the mod is mesh mod
        """
        slt_match_bytes = f"/Game/Chara/{self.char_id}/Costume[0-9]+/Material/Color([0-9]+)/{self.char_id}_base".encode()
        slot_search = [re.search(slt_match_bytes, asset.Data) for asset in self._assets]
        matches = []

        for search_groups in slot_search:
            if search_groups is not None:
                try:
                    matches.append(search_groups.groups(0)[0].decode("utf-8"))
                except IndexError as e:
                    raise SlotNotFoundError from e

        if not matches:
            e = "No matching slot string in pak file"
            raise SlotNotFoundError(e)
        else:
            # return mode of the matches list (most common)
            return mode(matches)

    def override_props(self, **kwargs) -> None:
        """
        Override the properties if they are not detected properly. It's important
        to call this method BEFORE staging otherwise the mod will be categorised
        incorrectly

        :param kwargs:
            is_mesh: is a mesh mod - mutually exclusive with colour mods
            char_id: three-letter character identification code
            slot: the slot of which the colour mod applies to
        """
        if kwargs.get("is_mesh") is not None:
            self.mesh = kwargs["is_mesh"]
        if kwargs.get("slot") is not None:
            self.slot = kwargs["slot"]
        if kwargs.get("char_id") is not None:
            self.char_id = kwargs["char_id"]

    def stage(self) -> None:
        """
        Place downloaded mod into the staging folder which will be copied
        from when ggmod.sync is called
        """
        stored_dir = os.path.join(MODS_DIR, self.name)

        util.create_dir(stored_dir)
        shutil.copy(self.pakfile, stored_dir)
        shutil.copy(self.sigfile, stored_dir)

        self.stored_dir = stored_dir
        self.staged = True

    def unstage(self):
        """
        Remove mod from staging folder
        """
        if not self.staged:
            e = "Cannot unstage a mod that is not staged"
            raise ValueError(e)

        pakfile = self.pakfile.strip(os.sep).split(os.sep)[-1]
        sigfile = self.sigfile.strip(os.sep).split(os.sep)[-1]

        os.remove(os.path.join(self.stored_dir, pakfile))
        os.remove(os.path.join(self.stored_dir, sigfile))
        os.removedirs(self.stored_dir)

        self.stored_dir = os.path.abspath(os.path.join(pakfile, os.pardir))

    def _convert_to_dict(self) -> str:
        """
        Convert to dict form to be put into a .json file
        and given as kwargs to __init__ upon loading from said
        file

        :returns: Dictionary of all arguments given to this class
        """
        self_data = {}
        self_data["name"] = self.name
        self_data["info"] = {
            "_sFile": self.filename,
            "_sDescription": self.description,
            "_tsDateAdded": self.ts_date_added,
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
    Intermediary thingy between ModPage and Mod
    """

    def __init__(self, name: str, info: Dict):
        self.name = name
        self._info = info
        self.filename = info["_sFile"]
        self.description = info["_sDescription"]
        self.ts_date_added = info["_tsDateAdded"]

        self._download_url = info["_sDownloadUrl"]
        self._download_path = os.path.join(DOWNLOAD_DIR, self.filename)
        self._mesh = None
        self._slot = None
        self._char_id = None

    def set_mesh(self, value: bool):
        self._mesh = value

    def set_slot(self, value: int):
        self._slot = value

    def set_char_id(self, value: str):
        self._char_id = value

    def download(self) -> Mod:
        """
        This is just to get the archives and extract them in a reasonable
        location

        :returns: Mod formed from downloaded files
        """
        if os.path.exists(self._download_path):
            logging.debug(f"Already downloaded mod at {self._download_path}")
        else:
            logging.debug(f"Downloading shiny new mod archive {self._download_path}")

            response = util.get_request(self._download_url)
            with open(self._download_path, "wb") as fp:
                fp.write(response.content)

        decomp_paths = util.decompress_into_dir(self._download_path, self.name)

        pakfile_filter = filter(lambda p: p.endswith(".pak"), decomp_paths)
        sigfile_filter = filter(lambda p: p.endswith(".sig"), decomp_paths)

        if not pakfile_filter:
            e = f"No pakfile (.pak) found in archive {self.filename}"
            raise FileNotFoundError(e)
        else:
            pakfile = list(pakfile_filter)[0]

        if not sigfile_filter:
            logging.warn("No sigfile (.sig) file found in archive {self.filename}")
            original_sigfile = os.path.join(MODULE_DIR, "sigfile.sig")
            sigfile = pakfile.replace(".pak", ".sig")
            shutil.copy(original_sigfile, sigfile)
        else:
            sigfile = list(sigfile_filter)[0]

        return Mod(
            self.name,
            self._info,
            pakfile,
            sigfile,
            self._mesh,
            self._slot,
            self._char_id,
        )


class ModPage:
    """
    Mods and mod metadata extracted from gamebanana webpages
    """

    def __init__(self, url: str):
        info_response = util.get_request(GB_INFO_URL.format(url.split("/")[-1]))
        page_response = util.get_request(url)

        webpage = bs4.BeautifulSoup(page_response.content, "html.parser")
        title_tag = webpage.find(lambda tag: tag.get("id") == "PageTitle")

        self.name = list(title_tag.children)[0].strip().lower()
        self.name = self.name.replace(" ", "-").replace("'", "")

        self.__files_data = info_response.json()["_aFiles"]
        self.__mods = [ModLink(self.name, info) for info in self.__files_data]

    def __iter__(self) -> Generator:
        yield from self.__mods

    def __len__(self) -> int:
        return len(self.__mods)

    def __getitem__(self, key) -> ModLink:
        logging.debug(f"Getting {key-1}th item from {self.__mods}")
        return self.__mods[key]


class ModDB:
    """
    Manage moddb.json stored mods - the stored JSON is a list of
    JSON objects that can be restored to fully functional Mod()
    python objects
    """

    def __init__(self):
        self.path = os.path.join(CACHE_DIR, "mod_db.json")

        if not os.path.exists(self.path):
            with open(self.path, "w") as fp:
                json.dump({"mods": []}, fp)

        self._file_ro = open(self.path, "r")
        self._db = json.load(self._file_ro)

    def store_mod(self, mod: Mod) -> None:
        """
        Stores a mod as an object in a JSON file

        :param mod: the mod to store in the file
        """
        mod_data = mod._convert_to_dict()
        new_db = self._db.copy()

        if mod_data not in new_db["mods"]:
            new_db["mods"].append(mod_data)

            with open(self.path, "w") as fp:
                json.dump(new_db, fp)
        else:
            return

    def get_mods(self) -> List[Mod]:
        """
        Returns all mods stored as objects in the JSON file

        :returns: list of stored Mod objects
        """
        mods = [Mod(**data) for data in self._db["mods"]]
        return mods

    def clear(self) -> None:
        """
        Clears all mods in mod_db.json
        """
        with open(self.path, "w") as fp:
            json.dump([], fp)
