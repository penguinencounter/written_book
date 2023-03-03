import enum
import os
import os.path
import re
import typing

from PIL import Image

from .exceptions import ValidationError
from .types import JSON


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


shared_asset_cache: typing.Dict[str, Image.Image] = {}


class AssetResource:
    """
    Represents an image asset that is used during the compositing process.
    """

    def __init__(
        self,
        source: str,
        crop: typing.Optional[typing.Tuple[int, int, int, int]] = None,
        source_image: typing.Optional[Image.Image] = None,
    ):
        self.source_path = _normalize(source)
        self._static = False
        self.source: Image.Image = source_image or self._load()
        if crop is None:
            self.crop: typing.Tuple[int, int, int, int] = (
                0,
                0,
                self.source.width,
                self.source.height,
            )
        else:
            self.crop: typing.Tuple[int, int, int, int] = crop

    def _load(self) -> Image.Image:
        """
        Load the source image into memory.
        :return:
        """
        if self._static:
            return self.source
        if self.source_path in shared_asset_cache:
            return shared_asset_cache[self.source_path]
        else:
            source: Image.Image = Image.open(self.source_path).convert("RGBA")
            source.load()
            shared_asset_cache[self.source_path] = self.source
            return source

    def get(self) -> Image.Image:
        """
        Get the source image, cropped.
        :return:
        """
        return self.source.crop(self.crop)

    @classmethod
    def import_(
        cls, json_body: JSON, theme_directory: typing.Optional[str] = None
    ) -> "AssetResource":
        """
        Import an AssetResource from JSON.
        This is the code side of #/definitions/sourced in the theme schema.
        Specification should be managed in the schema, then ported to here.
        :param json_body: JSON python representation, by json.load[s].
        :param theme_directory: Path of the theme file or None for the cwd
        :return: ...new
        """
        theme_directory = (
            theme_directory or os.getcwd()
        )  # ideally don't support this later
        if not isinstance(json_body, dict):
            raise ValidationError(
                f"JSON body for AssetResource should be a dict, not {type(json_body)}",
                2,
            )
        # required: source
        if "source" not in json_body:
            raise ValidationError('AssetResource(s) require a "source".', 1)
        source = json_body["source"]  # relative to theme file
        if not isinstance(source, str):
            raise ValidationError(
                f"JSON body for AssetResource source should be a string, not {type(source)}",
                2,
            )
        # IF there is a crop, it must be exactly four integers.
        if "crop" in json_body:
            crop = json_body["crop"]
            if not isinstance(crop, list):
                raise ValidationError(
                    f"JSON body for AssetResource crop should be a list, not {type(crop)}",
                    2,
                )
            if len(crop) != 4:
                raise ValidationError(
                    f'"crop" must be exactly 4 integers or omitted, got {len(crop)} instead',
                    2,
                )
            intermediate: typing.List[int] = []
            for crop_att in crop:
                try:
                    assert (
                        isinstance(crop_att, float) and crop_att.is_integer()
                    ) or isinstance(crop_att, int)
                    assert int(crop_att) >= 0
                    intermediate.append(int(crop_att))
                except (ValueError, AssertionError):
                    raise ValidationError(
                        f"The cropping value {crop_att} must be an integer that is at least 0.",
                        2,
                    )
            new_crop: typing.Optional[typing.Tuple[int, int, int, int]] = tuple(
                intermediate
            )
        else:
            new_crop = None
        # try to resolve the source path on the theme path if it's not absolute
        if not os.path.isabs(source):
            source = os.path.join(theme_directory, source)
        # ensure it's absolute and all that
        source = _normalize(source)
        return cls(source, new_crop)

    @classmethod
    def from_image(cls, image: Image.Image):
        i = cls("", None, image)
        i._static = True
        return i


class Feature:
    def __init__(self, asset: AssetResource):
        self._asset = asset


class Justify2D:
    @enum.unique
    class X(enum.Enum):
        LEFT = "left"
        CENTER = "center"
        RIGHT = "right"

        def __repr__(self):
            return f"{self.value}"

    @enum.unique
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


class Anchor2D:
    @enum.unique
    class AnchorMode(enum.Enum):
        INSIDE = "inside"
        OUTSIDE = "outside"
        EDGE = "edge"

    @enum.unique
    class X(enum.Enum):
        LEFT = "left", None
        CENTER = "center", None
        RIGHT = "right", None
        INSIDE_LEFT = "inside-left", ("outside",)
        INSIDE_RIGHT = "inside-right", ("outside",)

        def __repr__(self):
            return f"{self.value[0]}"

        @staticmethod
        def valid(x_anchor: "Anchor2D.X", anchor: "Anchor2D.AnchorMode") -> bool:
            return x_anchor.value[1] is None or anchor.value in x_anchor.value[1]

    @enum.unique
    class Y(enum.Enum):
        TOP = "top", None
        CENTER = "center", None
        BOTTOM = "bottom", None
        INSIDE_TOP = "inside-top", ("outside",)
        INSIDE_BOTTOM = "inside-bottom", ("outside",)

        def __repr__(self):
            return f"{self.value[0]}"

        @staticmethod
        def valid(y_anchor: "Anchor2D.Y", anchor: "Anchor2D.AnchorMode") -> bool:
            return y_anchor.value[1] is None or anchor.value in y_anchor.value[1]

    @staticmethod
    def valid(
        x_anchor: typing.Union[X, str],
        y_anchor: typing.Union[Y, str],
        anchor: typing.Union[AnchorMode, str],
    ) -> bool:
        if isinstance(x_anchor, str):
            x_anchor = Anchor2D.X(x_anchor.upper())
        if isinstance(y_anchor, str):
            y_anchor = Anchor2D.Y(y_anchor.upper())
        if isinstance(anchor, str):
            anchor = Anchor2D.AnchorMode(anchor.upper())
        return Anchor2D.X.valid(x_anchor, anchor) and Anchor2D.Y.valid(y_anchor, anchor)


@enum.unique
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


@enum.unique
class Direction(enum.Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"

    @classmethod
    def from_name(cls, name: str) -> "Direction":
        return {"horizontal": cls.HORIZONTAL, "vertical": cls.VERTICAL}[name.lower()]


class FeatureOverride:
    def __init__(self, asset: AssetResource):
        self.asset = asset


class Feature2DOverride(FeatureOverride):
    def __init__(self, asset: AssetResource, x: int, y: int):
        super().__init__(asset)
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
        overrides: typing.Optional[typing.List[Feature2DOverride]] = None,
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
                else:
                    tiled.paste(img, (x * img.width, y * img.height))

        # Crop to the desired size using the justification
        crop_from = [0, 0]
        if self.justifyX == Justify2D.X.CENTER:
            crop_from[0] = (tiled.width - width) // 2
        elif self.justifyX == Justify2D.X.RIGHT:
            crop_from[0] = tiled.width - width
        if self.justifyY == Justify2D.Y.CENTER:
            crop_from[1] = (tiled.height - height) // 2
        elif self.justifyY == Justify2D.Y.BOTTOM:
            crop_from[1] = tiled.height - height
        crop_to = [crop_from[0] + width, crop_from[1] + height]
        tiled = tiled.crop((crop_from[0], crop_from[1], crop_to[0], crop_to[1]))
        return tiled


class Feature1DOverride(FeatureOverride):
    def __init__(self, asset: AssetResource, x: int):
        super().__init__(asset)
        self.x = x


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
        self,
        asset: AssetResource,
        justify: typing.Union[str, Justify1D] = "center",
        direction: Direction = Direction.HORIZONTAL,
        overrides: typing.Optional[typing.List[Feature1DOverride]] = None,
    ):
        super().__init__(asset)
        if isinstance(justify, str):
            justify = Justify1D.from_name(justify)
        self.justify = justify
        self.direction = direction
        self.overrides: typing.Dict[int, Feature1DOverride] = {
            o.x: o for o in (overrides or [])
        }

    def tile(self, length: int):
        """
        Tile the asset to the given length.
        :param length: The length to tile to.
        :return: The tiled image.
        """
        img = self._asset.get()
        if self.direction == Direction.VERTICAL:
            img = img.transpose(Image.ROTATE_90)
        # Round up to the next multiple of the asset size...
        tiled = Image.new("RGBA", (odd(next_multiple(length, img.width)), img.height))
        tile_count = tiled.width // img.width
        # Calculate the "origin" tile
        center_pos = 0
        if self.justify == Justify1D.CENTER:
            center_pos = tile_count // 2
        elif self.justify == Justify1D.END:
            center_pos = tile_count - 1

        # Paste that thing all over the place
        for x in range(tile_count):
            vx = x - center_pos
            if vx in self.overrides:
                override = self.overrides[vx]
                tiled.paste(override.asset.get(), (x * img.width, 0))
            else:
                tiled.paste(img, (x * img.width, 0))

        # Crop to the desired size using the justification
        crop_from = 0
        if self.justify == Justify1D.CENTER:
            crop_from = (tiled.width - length) // 2
        elif self.justify == Justify1D.END:
            crop_from = tiled.width - length
        crop_to = crop_from + length
        tiled = tiled.crop((crop_from, 0, crop_to, img.height))
        if self.direction == Direction.VERTICAL:
            tiled = tiled.transpose(Image.ROTATE_270)
        return tiled


if __name__ == "__main__":
    pass
