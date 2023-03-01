import os

import pytest
from beet import run_beet
from lectern import Document
from pytest_insta import SnapshotFixture


@pytest.mark.parametrize("directory", os.listdir("examples"))
def test_build(snapshot: SnapshotFixture, directory: str):
    if os.path.isfile(f"examples/{directory}"):
        pytest.skip("Not a directory, so can't test examples on it.")
    with run_beet(directory=f"examples/{directory}") as ctx:
        document = ctx.inject(Document)
        document.markdown_serializer.flat = True
        assert snapshot("pack.md") == document
