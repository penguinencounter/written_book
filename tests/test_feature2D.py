import pytest
from PIL import Image

from written_book.asset_resource import Feature2D, Justify2D, AssetResource, Feature2DOverride

verbose = {
    "top left": (Justify2D.X.LEFT, Justify2D.Y.TOP),
    "top center": (Justify2D.X.CENTER, Justify2D.Y.TOP),
    "top right": (Justify2D.X.RIGHT, Justify2D.Y.TOP),
    "center left": (Justify2D.X.LEFT, Justify2D.Y.CENTER),
    "center center": (Justify2D.X.CENTER, Justify2D.Y.CENTER),
    "center right": (Justify2D.X.RIGHT, Justify2D.Y.CENTER),
    "bottom left": (Justify2D.X.LEFT, Justify2D.Y.BOTTOM),
    "bottom center": (Justify2D.X.CENTER, Justify2D.Y.BOTTOM),
    "bottom right": (Justify2D.X.RIGHT, Justify2D.Y.BOTTOM)
}
one_word = {
    "center": (Justify2D.X.CENTER, Justify2D.Y.CENTER),
    "left": (Justify2D.X.LEFT, Justify2D.Y.CENTER),
    "right": (Justify2D.X.RIGHT, Justify2D.Y.CENTER),
    "top": (Justify2D.X.CENTER, Justify2D.Y.TOP),
    "bottom": (Justify2D.X.CENTER, Justify2D.Y.BOTTOM)
}
all_anchors = {**verbose, **one_word}
dummy_image_16 = AssetResource.from_image(Image.new("RGBA", (16, 16), (255, 0, 0, 255)))
dummy_image_16_2 = AssetResource.from_image(Image.new("RGBA", (16, 16), (255, 255, 0, 255)))
dummy_image_32 = AssetResource.from_image(Image.new("RGBA", (32, 32), (0, 255, 0, 255)))
dummy_image_24 = AssetResource.from_image(Image.new("RGBA", (24, 24), (0, 0, 255, 255)))
override_16 = Feature2DOverride(dummy_image_16_2, 0, 0)
override_24 = Feature2DOverride(dummy_image_24, 0, 0)
override_32 = Feature2DOverride(dummy_image_32, 0, 0)


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_anchor_parsing(anchor, expected):
    assert Feature2D.get_justify(anchor) == expected


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_initializer(anchor, expected):
    assert Feature2D(dummy_image_16, anchor).justify == expected


def test_compatible_override():
    Feature2D(dummy_image_16, "top left", [override_16])


def test_incompatible_override():
    with pytest.raises(ValueError) as exec_info:
        Feature2D(dummy_image_16, "top left", [override_24])
    print("\nexception message:\n", exec_info.value.args[0])
