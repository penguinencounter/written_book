import os
from collections import defaultdict
from json import load
from typing import Dict, List, NamedTuple, Optional

import pytest

from written_book.types import JSONObject
from written_book.asset_resource import AssetResource


class JsonTestCase(NamedTuple):
    class Expect(NamedTuple):
        ok: bool
        errorType: Optional[str] = None

    expect: Expect
    test: JSONObject
    kwargs: JSONObject = {}


def compile_test_targets() -> Dict[str, List[JsonTestCase]]:
    SCHEMA_TEST_DIR = os.path.join("tests", "schema_tests")
    compiled: Dict[str, List[JsonTestCase]] = defaultdict(list)

    all_target_paths: List[str] = []
    for base, _, files in os.walk(SCHEMA_TEST_DIR):
        for f in files:
            if not f.endswith(".json"):
                continue
            all_target_paths.append(os.path.join(base, f))

    for path in all_target_paths:
        with open(path) as f:
            jtests = load(f)
            for test in jtests:
                tc = JsonTestCase(**test)
                compiled[
                    os.path.relpath(path, SCHEMA_TEST_DIR).replace("\\", "/")
                ].append(
                    tc
                )  # always forward slashes
    return compiled


compiled_tests = compile_test_targets()


@pytest.mark.parametrize("test_data", compiled_tests["asset_resource.json"])
def test_import_asset_resource(test_data: JsonTestCase):
    if test_data.expect.ok:
        AssetResource.import_(test_data.test)
