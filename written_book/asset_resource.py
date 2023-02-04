import enum
import os.path
import re
import typing

from PIL import Image


def _normalize(path: str) -> str:
    """
    Standardize a path to a file, hopefully making it the same regardless of relative paths.
    :param path: The path to normalize.
    :return: The normalized path.
    """
    return os.path.abspath(os.path.expanduser(path))


def next_multiple(value: int, multiple: int) -> int:
    """
    Get the next multiple of a number.
    :param value: The value to round up.
    :param multiple: The multiple to round up to.
    :return: The next multiple.
    """
    return value + (multiple - value % multiple)


def odd(value: int) -> int:
    """
    Get the next odd number.
    :param value: The value to round up.
    :return: The next odd number.
    """
    return value + 1 if value % 2 == 0 else value


shared_asset_cache = {}


class AssetResource:
    """
    Represents an image asset that is used during the compositing process.
    """

    def __init__(self, source: str, crop: typing.Tuple[int, int, int, int] = None):
        self.source_path = _normalize(source)
        self.source: typing.Optional[Image.Image] = None
        self._static = False
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
        if self._static:
            return self.source
        if self.source_path in shared_asset_cache:
            self.source = shared_asset_cache[self.source_path]
            return
        else:
            self.source = Image.open(self.source_path).convert("RGBA")
            self.source.load()
            shared_asset_cache[self.source_path] = self.source

    def get(self) -> Image.Image:
        """
        Get the source image, loading it into memory if necessary.
        :return:
        """
        if self.source is None:
            self._load()
        return self.source.crop(self.crop)

    def destroy(self, for_all: bool = False):
        """
        Destroy the source image to free up memory.
        :return:
        """
        if self._static:
            return
        self.source = None
        if for_all and self.source_path in shared_asset_cache:
            del shared_asset_cache[self.source_path]

    @classmethod
    def from_image(cls, image: Image.Image):
        i = cls("", (0, 0, 0, 0))
        i.source = image
        i._static = True
        i.crop = (0, 0, image.width, image.height)
        return i


class Feature:
    def __init__(self, asset: AssetResource):
        self._asset = asset


class Justify2D:
    class X(enum.Enum):
        LEFT = "left"
        CENTER = "center"
        RIGHT = "right"

        def __repr__(self):
            return f"{self.value}"

    class Y(enum.Enum):
        TOP = "top"
        CENTER = "center"
        BOTTOM = "bottom"

        def __repr__(self):
            return f"{self.value}"

    one_word_aliases = {
        "center": ("center", "center"),
        "left": ("center", "left"),
        "right": ("center", "right"),
        "top": ("top", "center"),
        "bottom": ("bottom", "center"),
    }

    x_word = {"left": X.LEFT, "center": X.CENTER, "right": X.RIGHT}

    y_word = {"top": Y.TOP, "center": Y.CENTER, "bottom": Y.BOTTOM}


class Justify1D(enum.Enum):
    START = "start"
    CENTER = "center"
    END = "end"

    @classmethod
    def from_name(cls, name: str) -> "Justify1D":
        return {
            "start": cls.START,
            "center": cls.CENTER,
            "end": cls.END,
            "left": cls.START,
            "right": cls.END,
            "top": cls.START,
            "bottom": cls.END,
        }[name.lower()]


class Feature2DOverride:
    def __init__(self, asset: AssetResource, x: int, y: int):
        self.asset = asset
        self.x = x
        self.y = y


class Feature2D(Feature):
    @staticmethod
    def get_justify(code: str) -> typing.Tuple[Justify2D.X, Justify2D.Y]:
        """
        Get the justification enums from a justification code.
        Test coverage @ tests/test_feature2D.py
        :param code: string like "top left" or similar
        :return: (x justify, y justify)
        """
        words = re.findall(
            r"(?:^|(?<=[^A-Za-z0-9]))(\w+)(?=[^A-Za-z0-9]|$)", code.lower()
        )
        if 1 < len(words) > 2:
            raise ValueError(
                f"Invalid justify code: {code}; must be 1 or 2 words, got {len(words)}"
            )
        if len(words) == 1:
            if words[0] in Justify2D.one_word_aliases:
                words = Justify2D.one_word_aliases[words[0]]
            else:
                raise ValueError(
                    f"Invalid justify code: {code}; the 1-word code '{words[0]}' is not supported"
                )
        justify = Justify2D.x_word[words[1]], Justify2D.y_word[words[0]]
        return justify

    def __init__(
        self,
        asset: AssetResource,
        justify: typing.Union[str, typing.Tuple[Justify2D.X, Justify2D.Y]] = "center",
        overrides: typing.List[Feature2DOverride] = None,
    ):
        super().__init__(asset)
        if isinstance(justify, str):
            justify = self.get_justify(justify)
        self.justifyX, self.justifyY = justify
        self.overrides: typing.Dict[typing.Tuple[int, int], Feature2DOverride] = {
            (o.x, o.y): o for o in (overrides or [])
        }
        for override in self.overrides.values():
            if override.asset.get().size != self._asset.get().size:
                raise ValueError(
                    "Override asset size must match the base asset size.\n    "
                    f"got {override.asset.get().size}, expected {self._asset.get().size}\n    "
                    "(hint: try resizing the override with the 'crop' option)\n    "
                    "(hint: if you don't want to do that, use an overlay instead)"
                )
            override.asset.destroy()  # We don't need the image right now

    @property
    def justify(self) -> typing.Tuple[Justify2D.X, Justify2D.Y]:
        return self.justifyX, self.justifyY

    def tile(self, width: int, height: int):
        """
        Tile the asset to the given dimensions.
        :param width: The width to tile to.
        :param height: The height to tile to.
        :return: The tiled image.
        """
        img = self._asset.get()
        # Round up to the next multiple of the asset size...
        tiled = Image.new(
            "RGBA",
            (
                odd(next_multiple(width, img.width)),
                odd(next_multiple(height, img.height)),
            ),
        )
        tile_count = tiled.width // img.width, tiled.height // img.height
        # Calculate the "origin" tile
        center_pos = [0, 0]
        if self.justifyX == Justify2D.X.CENTER:
            center_pos[0] = tile_count[0] // 2
        elif self.justifyX == Justify2D.X.RIGHT:
            center_pos[0] = tile_count[0] - 1
        if self.justifyY == Justify2D.Y.CENTER:
            center_pos[1] = tile_count[1] // 2
        elif self.justifyY == Justify2D.Y.BOTTOM:
            center_pos[1] = tile_count[1] - 1

        # Paste that thing all over the place
        for x in range(tile_count[0]):
            for y in range(tile_count[1]):
                vx, vy = x - center_pos[0], y - center_pos[1]
                if (vx, vy) in self.overrides:
                    override = self.overrides[(vx, vy)]
                    tiled.paste(override.asset.get(), (x * img.width, y * img.height))

        return tiled


class Feature1D(Feature):
    @staticmethod
    def get_justify(code: str) -> Justify1D:
        """
        Get the justification enum from a justification code.
        Test coverage @ tests/test_feature1D.py
        :param code: string like "top" or similar
        :return: justify enum
        """
        return Justify1D.from_name(code)

    def __init__(
        self, asset: AssetResource, justify: typing.Union[str, Justify1D] = "center"
    ):
        super().__init__(asset)
        if isinstance(justify, str):
            justify = Justify1D.from_name(justify)
        self.justify = justify


if __name__ == "__main__":
    pass
