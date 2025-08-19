"""
Duplicate of test_typedattr_numpy.py with added future annotations.
"""

# pylint: disable=duplicate-code

from __future__ import annotations

from copy import deepcopy
from typing import List

import attrs
import pytest

from typedparser import attrs_from_dict, definenumpy
from typedparser.objects import flatten_dict

np = pytest.importorskip("numpy", reason="Skipping numpy tests because numpy is not installed.")


@definenumpy
class CfgWithNumpy:
    f1: np.ndarray = np.array([1, 7])
    f2: np.ndarray = np.array([[2, 4]])
    f3: List[np.ndarray] = [np.array([1, 2]), np.array([3, 4])]


_ref_cfg_with_numpy = {
    "f1": np.array([1, 7]),
    "f2": np.array([[2, 4]]),
    "f3": [np.array([1, 2]), np.array([3, 4])],
}

_REMOVE_KEY = f"__{__name__}_REMOVE_KEY__"


@pytest.fixture(
    params=[
        (
            {"f1": 30, "f2": np.array([1, 6])},
            CfgWithNumpy,
            TypeError,
            {"f3": _ref_cfg_with_numpy["f3"]},
        ),
        ({}, CfgWithNumpy, None, _ref_cfg_with_numpy),
    ]
)
def fixture_test_cases(request):
    yield request.param


def _create_ref_dict(input_dict, expected_input_update):
    ref_dict = deepcopy(input_dict)
    ref_dict.update(expected_input_update)
    for k in list(ref_dict.keys()):
        val = ref_dict[k]
        if isinstance(val, str) and val == _REMOVE_KEY:
            del ref_dict[k]
    return ref_dict


def test_typedattr_numpy(fixture_test_cases):
    input_dict, cfg_class, expected_error, expected_input_update = fixture_test_cases
    # note: if there is an expected_error, the final comparison will be between
    # output with strict=False, otherwise with strict=True
    ref_dict = _create_ref_dict(input_dict, expected_input_update)

    print(f"===================== test input {input_dict} class {cfg_class}")
    if expected_error is not None:
        print(f"---------- Expected to raise {expected_error}")
        with pytest.raises(expected_error):
            attrs_from_dict(cfg_class, input_dict, strict=True)

        print(f"---------- Expected to work when strict=False")
        c = attrs_from_dict(cfg_class, input_dict, strict=False)
    else:
        print(f"---------- Expected to work when strict=True")
        c = attrs_from_dict(cfg_class, input_dict, strict=True)
    print(f"Got {c}")
    print(f"          asserting output")
    cand_dict = attrs.asdict(c)

    ref_dict_flat = flatten_dict(ref_dict)
    cand_dict_flat = flatten_dict(cand_dict)
    all_values = list(ref_dict_flat.values()) + list(cand_dict_flat.values())
    if any(isinstance(v, np.ndarray) for v in all_values):
        # special case: numpy must be compared with .all()
        assert set(ref_dict_flat.keys()) == set(
            cand_dict_flat.keys()
        ), f"Mismatch in flat keys. Original dicts: {ref_dict} != {cand_dict}"
        print(f"Ref  flat {ref_dict}")
        print(f"Cand flat {cand_dict}")
        for k, v_ref in ref_dict_flat.items():
            v_cand = cand_dict_flat[k]
            if isinstance(v_ref, np.ndarray):
                assert (v_cand == v_ref).all()  # pylint: disable=no-member # noqa
                continue
            assert v_cand == v_ref
    else:
        # in other cases the dict comparison works out
        print(f"Ref  {ref_dict}")
        print(f"Cand {cand_dict}")
        assert cand_dict == ref_dict
    print()


@definenumpy
class CfgNumpyLocal:
    f1: np.ndarray = np.array([1, 7])


def test_numpy_comparison():
    c1 = CfgNumpyLocal()
    c2 = CfgNumpyLocal()
    assert c1 == c2
    c3 = CfgNumpyLocal(f1=np.array([1, 7]))
    assert c1 == c3
    c4 = CfgNumpyLocal(f1=np.array([1, 8]))
    assert c1 != c4
