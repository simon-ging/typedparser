import dataclasses

from typedparser.objects import (
    inspect_obj,
    analyze_flat_object,
    analyze_nested_object_structure,
    print_datapoint,
    print_item_recursively,
)


# A dummy class to test inspect_obj.
class Dummy:
    def __init__(self):
        self.x = 10
        self.y = "hello"

    def foo(self):
        return "bar"


def test_inspect_obj(capsys):
    d = Dummy()
    inspect_obj(d)
    # The expected output is sorted by the type names and then attribute names.
    # For Dummy:
    #   - d.x is an int  → "int x"
    #   - d.foo is a bound method → "method foo"
    #   - d.y is a str  → "str y"
    # Sorted alphabetically by type: "int", "method", "str".
    expected_output = """\
int x
method foo
str y
"""
    assert inspect_obj(d) == expected_output


@dataclasses.dataclass
class Person:
    name: str
    age: int


def convert_dataclass_instance_to_dict(d_instance, d_class) -> dict:
    return {k: getattr(d_instance, k) for k in d_class.__dataclass_fields__.keys()}


def test_convert_dataclass_instance_to_dict():
    # Create an instance of the dataclass.
    person = Person(name="Alice", age=30)
    # Convert the instance to a dict.
    result = convert_dataclass_instance_to_dict(person, Person)
    # Define the expected dictionary.
    expected = {"name": "Alice", "age": 30}
    # Verify that the conversion matches the expected output.
    assert result == expected


# --- Dummy Classes for Testing ---


class DummyArray:
    """A dummy object mimicking an array with shape and dtype attributes."""

    def __init__(self, shape, dtype, repr_str):
        self.shape = shape
        self.dtype = dtype
        self.repr_str = repr_str

    def __str__(self):
        return self.repr_str


class DummyArrayForPrint:
    """Another dummy array type for testing print_datapoint."""

    def __init__(self, shape, dtype):
        self.shape = shape
        self.dtype = dtype


# --- Tests for analyze_flat_object ---


def test_analyze_flat_object_with_shape_dtype():
    dummy = DummyArray(shape=(2, 3), dtype="float32", repr_str="dummy_array")
    # Expected output: first the shape and dtype info then the truncated string.
    expected = f"shape={(2, 3)} dtype=float32 dummy_array"
    result = analyze_flat_object(dummy)
    assert result == expected


def test_analyze_flat_object_with_len():
    value = [1, 2, 3]
    # List has __len__; expected to show its length and then its string representation.
    expected = f"len=3 {str(value)}"
    result = analyze_flat_object(value)
    assert result == expected


def test_analyze_flat_object_leaf():
    value = 5
    # An integer doesn't have __len__ or shape, so only its string is returned.
    expected = str(value)
    result = analyze_flat_object(value)
    assert result == expected


# --- Tests for analyze_nested_object_structure ---


def test_analyze_nested_object_structure_mapping():
    # A dict: only the first key-value pair is processed.
    data = {"a": [1, 2, 3]}
    # For key 'a', the value [1, 2, 3] is a list.
    # The list branch processes its first element (1) as a leaf.
    # analyze_flat_object(1) returns "1", so:
    # list branch: " list #0:  1"  (note the extra space from the leaf branch)
    # mapping branch: " dict a ->  list #0:  1"
    expected = " dict a ->  list #0:  1"
    result = analyze_nested_object_structure(data)
    assert result == expected


def test_analyze_nested_object_structure_list():
    data = [1, 2, 3]
    # List branch processes the first element.
    expected = " list #0:  1"
    result = analyze_nested_object_structure(data)
    assert result == expected


def test_analyze_nested_object_structure_leaf():
    data = 42
    # A leaf: returns " " + analyze_flat_object(42)
    expected = " " + str(42)
    result = analyze_nested_object_structure(data)
    assert result == expected


# --- Test for print_datapoint ---


def test_print_datapoint(capsys):
    dummy = DummyArrayForPrint(shape=(10, 10), dtype="int64")
    dp = {"a": dummy, "b": [1, 2, 3, 4, 5, 6], "c": "hello"}
    print_datapoint(dp)
    captured = capsys.readouterr().out
    expected_lines = [
        f"    a: shape={(10, 10)} dtype=int64",
        f"    b: len=6 {[1, 2, 3, 4, 5]}...",
        f"    c: class=str hello",
    ]
    expected_output = "\n".join(expected_lines) + "\n"
    assert captured == expected_output


# --- Test for print_item_recursively ---


def test_print_item_recursively(capsys):
    # Create a nested structure:
    # {
    #   "a": [1, {"b": "hello"}]
    # }
    item = {"a": [1, {"b": "hello"}]}
    print_item_recursively(item)
    captured = capsys.readouterr().out
    # Expected output (each line printed on its own):
    # a
    #     1 (int)
    #     b
    #       hello (str)
    expected_lines = ["a", "    1 (int)", "    b", "      hello (str)"]
    expected_output = "\n".join(expected_lines) + "\n"
    assert captured == expected_output
