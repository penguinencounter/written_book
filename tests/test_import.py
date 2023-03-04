import os
import pprint
from collections import defaultdict
from json import load
from typing import Any, Callable, Dict, List, NamedTuple

import pytest

from written_book.asset_resource import AssetResource, Feature
from written_book.types import JSONObject


class JsonTestCase(NamedTuple):
    class Expect(NamedTuple):
        ok: bool
        errorType: str = ""

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
                assert "expect" in test
                assert "test" in test
                exp = test.pop("expect")
                exp = JsonTestCase.Expect(**exp)
                tc = JsonTestCase(**test, expect=exp)
                compiled[
                    os.path.relpath(path, SCHEMA_TEST_DIR).replace("\\", "/")
                ].append(
                    tc
                )  # always forward slashes
    return compiled


compiled_tests = compile_test_targets()


def dump_test_case(jtc: JsonTestCase):
    print(f"\nTest case details:")
    if not jtc.expect.ok:
        print(f"  [{jtc.expect.errorType} expected]")
    print(f"  Test input:")
    test_str = pprint.pformat(jtc.test, indent=1)
    # indent everything
    for line in test_str.splitlines():
        print(f"    {line}")
    print(f"  Test args:")
    for key, val in jtc.kwargs.items():
        print(f"    {key} = {pprint.pformat(val, indent=1, compact=True)}")


def run_test(jtc: JsonTestCase, target_func: Callable[..., Any]):
    if jtc.expect.ok:
        target_func(jtc.test, **jtc.kwargs)
    else:
        with pytest.raises(Exception) as e:
            target_func(jtc.test, **jtc.kwargs)
        print(" (error message):\n", e.value)
        assert jtc.expect.errorType in e.value.__class__.__name__


@pytest.mark.parametrize("test_data", compiled_tests["asset_resource.json"])
def test_import_asset_resource(test_data: JsonTestCase):
    dump_test_case(test_data)
    run_test(test_data, AssetResource.import_)


@pytest.mark.parametrize("test_data", compiled_tests["feature.json"])
def test_import_feature(test_data: JsonTestCase):
    dump_test_case(test_data)
    run_test(test_data, Feature.import_)
