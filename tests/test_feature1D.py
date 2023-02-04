import pytest

from written_book.asset_resource import Feature1D, Justify1D, AssetResource

all_anchors = {
    "start": Justify1D.START,
    "center": Justify1D.CENTER,
    "end": Justify1D.END,
    "left": Justify1D.START,
    "right": Justify1D.END,
    "top": Justify1D.START,
    "bottom": Justify1D.END
}
dummy_asset = AssetResource(".", (0, 0, 0, 0))


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_anchor_parsing(anchor, expected):
    assert Justify1D.from_name(anchor) == expected


@pytest.mark.parametrize("anchor,expected", all_anchors.items())
def test_initializer(anchor, expected):
    assert Feature1D(dummy_asset, anchor).justify == expected
