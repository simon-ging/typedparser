import numpy as np
import pytest

from typedparser.objects import modify_nested_object, flatten_dict


@pytest.mark.parametrize("input_object, expected_object", [
    pytest.param({"sub": {"str_val": "value"}, "int_vals": [1, 2]},
                 {"sub": {"str_val": "value_mod"}, "int_vals": [2, 4]},
                 id="nested"),
    pytest.param([np.array([1, 2]), np.array([3, 4])],
                 [[1, 2], [3, 4]],
                 id="numpytolist"),
    pytest.param("not_nested",
                 "not_nested_mod",
                 id="flat"),
])
def test_nested_objects(input_object, expected_object):
    modified_object = modify_nested_object(input_object, _modifier_fn, return_copy=True)
    assert modified_object == expected_object


@pytest.mark.parametrize("input_object, expected_exception", [
    pytest.param(set((7, 7, 2, "something")), TypeError, id="set"),
    pytest.param(tuple((7, 7, 2, "something")), TypeError, id="tuple"),
])
def test_nested_objects_failures(input_object, expected_exception):
    with pytest.raises(expected_exception):
        modify_nested_object(input_object, _modifier_fn, return_copy=True)


def _modifier_fn(obj):
    if isinstance(obj, int):
        return obj * 2
    if isinstance(obj, str):
        return f"{obj}_mod"
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise ValueError(f"Unknown leaf type: {type(obj)}")


@pytest.mark.parametrize("input_dict, flat_ref, expected_error", [
    pytest.param({"a": 1, "b": {"c": [2, 3], "d": 4}}, {"a": 1, "b/c#0": 2, "b/c#1": 3, "b/d": 4},
                 None, id="nested1"),
    pytest.param({"a": 1, "b": [2, 3]}, {"a": 1, "b#0": 2, "b#1": 3}, None, id="nested2"),
    pytest.param({'a': 1, 'b': {'c': 2, 'd': 3}, 'e': [1, 2, "6"]},
                 {'a': 1, 'b/c': 2, 'b/d': 3, 'e#0': 1, 'e#1': 2, 'e#2': '6'},
                 None, id="docstring"),
    pytest.param({"a": 1, "b": {"c": 2, "d": 3}}, {"a": 1, "b/c": 2, "b/d": 3}, None,
                 id="nested_no_list"),
    pytest.param({"a": 1, "b": 2}, {"a": 1, "b": 2}, None, id="flat"),
])
def test_flatten_dict_with_lists(input_dict, flat_ref, expected_error):
    assert expected_error is None, "Test not implemented"
    flat_cand = flatten_dict(input_dict)
    print(f"Cand: {flat_cand}")
    print(f"Ref:  {flat_ref}")
    assert flat_cand == flat_ref
