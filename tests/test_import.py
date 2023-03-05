import copy
import itertools
import os
import pprint
from collections import defaultdict
from json import load
from typing import Any, Callable, Dict, List, NamedTuple, cast, Tuple

import pytest

from written_book.asset_resource import AssetResource, Feature, Feature2D
from written_book.types import JSON, JSONObject


class JsonTestCase(NamedTuple):
    class Expect(NamedTuple):
        ok: bool
        errorType: str = ""

    expect: Expect
    test: JSON
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
            jtests: List[JSONObject] = load(f)
            for test in jtests:
                assert "expect" in test
                assert "test" in test
                exp_j = test.pop("expect")
                exp = JsonTestCase.Expect(**exp_j)  # type: ignore
                # type checker sucks for this sort of thing.
                # the test suite is supposed to be quick and dirty, not safe.
                iterate: Dict[str, List[JSON]] = cast(
                    Dict[str, List[JSON]], test.pop("iterate", {})
                )
                # apply the key to all the values, so (key, value), (key, value), ...
                bound: List[List[Tuple[str, JSON]]] = []
                for key, values in iterate.items():
                    bound.append([(key, v) for v in values])
                # permute all the values
                for perm in itertools.product(*bound):
                    tmod = copy.deepcopy(test)
                    # attach permutations
                    if isinstance(tmod["test"], dict):
                        new_test: JSONObject = tmod["test"]
                        new_test.update({k: v for k, v in perm})
                        tmod["test"] = new_test
                    tc = JsonTestCase(**tmod, expect=exp)
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


@pytest.mark.parametrize("test_data", compiled_tests["feature2d.json"])
def test_import_feature2d(test_data: JsonTestCase):
    dump_test_case(test_data)
    run_test(test_data, Feature2D.import_)
