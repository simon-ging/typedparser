import pytest
from attr import define

from typedparser.objects import (
    big_obj_to_short_str,
    check_object_equality,
    compare_nested_objects,
    flatten_dict,
    get_all_base_classes,
    get_attr_names,
    invert_dict_of_dict,
    invert_list_of_dict,
    is_any_iterable,
    is_any_mapping,
    is_iterable,
    is_standard_iterable,
    is_standard_mapping,
    modify_nested_object,
    repr_value,
)


@pytest.mark.parametrize(
    "input_object, expected_object",
    [
        pytest.param(
            {"sub": {"str_val": "value"}, "int_vals": [1, 2]},
            {"sub": {"str_val": "value_mod"}, "int_vals": [2, 4]},
            id="nested",
        ),
        pytest.param("not_nested", "not_nested_mod", id="flat"),
    ],
)
def test_nested_objects(input_object, expected_object):
    modified_object = modify_nested_object(input_object, _modifier_fn, return_copy=True)
    assert modified_object == expected_object


@pytest.mark.parametrize(
    "input_object",
    [
        pytest.param(set((7, 7, 2, "something")), id="set"),
        pytest.param(tuple((7, 7, 2, "something")), id="tuple"),
    ],
)
def test_nested_objects_with_unmodifiables(input_object):
    modify_nested_object(input_object, _modifier_fn, return_copy=True)


def _modifier_fn(obj):
    if isinstance(obj, int):
        return obj * 2
    if isinstance(obj, str):
        return f"{obj}_mod"
    raise ValueError(f"Unknown leaf type: {type(obj)}")


@pytest.mark.parametrize(
    "input_dict, flat_ref, expected_error",
    [
        pytest.param(
            {"a": 1, "b": {"c": [2, 3], "d": 4}},
            {"a": 1, "b/c#0": 2, "b/c#1": 3, "b/d": 4},
            None,
            id="nested1",
        ),
        pytest.param({"a": 1, "b": [2, 3]}, {"a": 1, "b#0": 2, "b#1": 3}, None, id="nested2"),
        pytest.param(
            {"a": 1, "b": {"c": 2, "d": 3}, "e": [1, 2, "6"]},
            {"a": 1, "b/c": 2, "b/d": 3, "e#0": 1, "e#1": 2, "e#2": "6"},
            None,
            id="docstring",
        ),
        pytest.param(
            {"a": 1, "b": {"c": 2, "d": 3}},
            {"a": 1, "b/c": 2, "b/d": 3},
            None,
            id="nested_no_list",
        ),
        pytest.param({"a": 1, "b": 2}, {"a": 1, "b": 2}, None, id="flat"),
    ],
)
def test_flatten_dict_with_lists(input_dict, flat_ref, expected_error):
    assert expected_error is None, "Test not implemented"
    flat_cand = flatten_dict(input_dict)
    print(f"Cand: {flat_cand}")
    print(f"Ref:  {flat_ref}")
    assert flat_cand == flat_ref


# invert_dict_of_dict


def test_simple_inversion():
    input_dict = {"a": {"x": 1, "y": 2}, "b": {"x": 3, "y": 4}}
    expected_output = {"x": {"a": 1, "b": 3}, "y": {"a": 2, "b": 4}}
    assert invert_dict_of_dict(input_dict) == expected_output


def test_empty_dictionary():
    assert invert_dict_of_dict({}) == {}


def test_nested_same_values():
    input_dict = {"a": {"x": 1}, "b": {"x": 1}}
    expected_output = {"x": {"a": 1, "b": 1}}
    assert invert_dict_of_dict(input_dict) == expected_output


def test_non_string_keys():
    input_dict = {1: {"x": 1}, 2: {"x": 2}}
    expected_output = {"x": {1: 1, 2: 2}}
    assert invert_dict_of_dict(input_dict) == expected_output


def test_invalid_input():
    with pytest.raises(AttributeError):
        invert_dict_of_dict("not a dict")


def test_immutability():
    input_dict = {"a": {"x": 1}}
    invert_dict_of_dict(input_dict)
    assert input_dict == {"a": {"x": 1}}


# invert_list_of_dict


def test_normal_case():
    input_list = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    expected_output = {"a": [1, 3], "b": [2, 4]}
    assert invert_list_of_dict(input_list) == expected_output


def test_empty_list():
    assert invert_list_of_dict([]) == {}


def test_list_with_empty_dict():
    assert invert_list_of_dict([{}, {}]) == {}


def test_list_with_non_dict_element():
    with pytest.raises(AttributeError):
        invert_list_of_dict([{"a": 1}, "not a dict"])


def test_dicts_with_different_keys():
    input_list = [{"a": 1}, {"b": 2}]
    expected_output = {"a": [1], "b": [2]}
    assert invert_list_of_dict(input_list) == expected_output


@define
class SampleClass:
    attr1: int
    attr2: str


def test_get_attr_names():
    names = get_attr_names(SampleClass)
    assert set(names) == {"attr1", "attr2"}


def test_flatten_dict():
    input_dict = {"a": 1, "b": {"c": 2, "d": 3}}
    expected_output = {"a": 1, "b/c": 2, "b/d": 3}
    assert flatten_dict(input_dict) == expected_output


def test_invert_dict_of_dict():
    input_dict = {"a": {"x": 1, "y": 2}, "b": {"x": 3, "y": 4}}
    expected_output = {"x": {"a": 1, "b": 3}, "y": {"a": 2, "b": 4}}
    assert invert_dict_of_dict(input_dict) == expected_output


def test_invert_list_of_dict():
    input_list = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    expected_output = {"a": [1, 3], "b": [2, 4]}
    assert invert_list_of_dict(input_list) == expected_output


class BaseClass:
    pass


class DerivedClass(BaseClass):
    pass


def test_get_all_base_classes():
    bases = list(get_all_base_classes(DerivedClass))
    print(bases)
    assert bases == [BaseClass]


def test_is_standard_mapping():
    assert is_standard_mapping({"key": "value"})
    assert not is_standard_mapping([1, 2, 3])
    assert not is_standard_mapping("not a dict")


def test_is_standard_iterable():
    assert is_standard_iterable([1, 2, 3])
    assert is_standard_iterable((1, 2, 3))
    assert not is_standard_iterable("string")
    assert not is_standard_iterable(123)


def test_is_any_mapping():
    assert is_any_mapping({"key": "value"})
    assert not is_any_mapping([1, 2, 3])
    assert not is_any_mapping("not a dict")


def test_is_any_iterable():
    assert is_any_iterable([1, 2, 3])
    assert is_any_iterable((1, 2, 3))
    assert is_any_iterable("string")
    assert not is_any_iterable(123)


def test_is_iterable():
    assert is_iterable([1, 2, 3])
    assert is_iterable((1, 2, 3))
    assert not is_iterable("string")
    assert not is_iterable(123)


def test_check_object_equality():
    assert check_object_equality({"a": 1}, {"a": 1})
    assert not check_object_equality({"a": 1}, {"a": 2})


def test_big_obj_to_short_str():
    assert big_obj_to_short_str(None) == "None"
    assert big_obj_to_short_str({"key": "value"}) == "dict len 1"
    assert big_obj_to_short_str([1, 2, 3]) == "list len 3"


def test_compare_nested_objects():
    obj1 = {"a": 1, "b": {"c": 2, "d": 3}}
    obj2 = {"a": 1, "b": {"c": 2, "d": 3}}
    obj3 = {"a": 1, "b": {"c": 2, "d": 4}}
    obj4 = {"a": 1, "b": {"c": 2}}

    assert compare_nested_objects(obj1, obj2) == []
    assert compare_nested_objects(obj1, obj3) != []
    assert compare_nested_objects(obj1, obj4) != []


def test_repr_value_simple_list():
    dct = [1.0, 3.0, 4.0, 5.0, 6.0]
    result = repr_value(dct)
    expected = """list len=5
  float: 1.0
  float: 3.0
  float: 4.0
  ..."""
    assert result == expected


def test_repr_value_nested_list():
    dct = [[1.0, 3.0, 4.0, 5.0, 6.0], [1.0, 3.0, 4.0, 5.0, 6.0]]
    result = repr_value(dct)
    expected = """list len=2
  list len=5
    float: 1.0
    float: 3.0
    float: 4.0
    ...
  list len=5
    float: 1.0
    float: 3.0
    float: 4.0
    ..."""
    assert result == expected


def test_repr_value_list_of_dicts():
    data = [
        {
            "name": "Alice",
            "age": 29,
            "city": "New York",
            "email": "alice@example.com",
            "is_active": True,
            "hobbies": ["reading", "traveling"],
            "score": 85.5,
        },
        {
            "name": "Bob",
            "age": 35,
            "city": "San Francisco",
            "email": "bob@example.com",
            "is_active": False,
            "hobbies": ["cycling", "cooking"],
            "score": 90.3,
        },
    ]
    result = repr_value(data)
    # Since the output is quite long, we'll check key parts of it
    assert "list len=2" in result
    assert "dict len=7" in result
    assert "name: str len=5: Alice" in result
    assert "name: str len=3: Bob" in result
    assert "hobbies" in result
    assert "score" in result


def test_repr_value_nested_dicts():
    dct = [{"floats": [1.0, 3.0, 4.0, 5.0, 6.0]}, {"something": "else"}]
    result = repr_value(dct)
    # Check key parts of the output
    assert "list len=2" in result
    assert "dict len=1" in result
    assert "floats" in result
    assert "something" in result
    assert "else" in result
