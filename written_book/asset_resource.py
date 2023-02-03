import enum
import typing

from PIL import Image


class Justify(enum.Enum):
    EDGE1 = enum.auto()
    EDGE2 = enum.auto()
    CENTER = enum.auto()


class AssetResource:
    """
    Represents an image asset that is used during the compositing process.
    """
    def __init__(self, source: str, crop: typing.Tuple[int, int, int, int] = None, justify: Justify = Justify.EDGE1):
        self.source_path = source
        self.source: typing.Optional[Image.Image] = None
        if crop is None:
            self._load()
            self.crop = (0, 0, self.source.width, self.source.height)
            self.destroy()
        else:
            self.crop = crop

    def _load(self):
        """
        Load the source image into memory.
        :return:
        """
        self.source = Image.open(self.source_path).convert("RGBA")
        self.source.load()

    def destroy(self):
        """
        Destroy the source image to free up memory.
        :return:
        """
        self.source = None  # and let the garbage collector do its job
