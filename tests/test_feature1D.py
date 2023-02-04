import pytest
from PIL import Image

from written_book.asset_resource import AssetResource, Feature1D, Justify1D

all_anchors = {
    "start": Justify1D.START,
    "center": Justify1D.CENTER,
    "end": Justify1D.END,
    "left": Justify1D.START,
    "right": Justify1D.END,
    "top": Justify1D.START,
    "bottom": Justify1D.END,
}
dummy_image = Image.new("RGBA", (4, 16), (255, 0, 0, 0))
dummy_asset = AssetResource.from_image(dummy_image)


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_anchor_parsing(anchor: str, expected: Justify1D):
    assert Justify1D.from_name(anchor) == expected


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_initializer(anchor: str, expected: Justify1D):
    assert Feature1D(dummy_asset, anchor).justify == expected
