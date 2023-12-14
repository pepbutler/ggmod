class CharNotFoundError(Exception):
    """
    Character string has not been found - could be a UI mod, for example
    """


class SlotNotFoundError(Exception):
    """
    Colour slot could not be identified even though the mod is identified
    as a colour slot mod
    """

