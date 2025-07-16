import pytest

from typedparser.objects import modify_nested_object

np = pytest.importorskip("numpy", reason="Skipping numpy tests because numpy is not installed.")


@pytest.mark.parametrize(
    "input_object, expected_object",
    [
        pytest.param([np.array([1, 2]), np.array([3, 4])], [[1, 2], [3, 4]], id="numpytolist"),
    ],
)
def test_nested_objects_numpy(input_object, expected_object):
    modified_object = modify_nested_object(input_object, _modifier_fn, return_copy=True)
    assert modified_object == expected_object


def _modifier_fn(obj):
    if isinstance(obj, int):
        return obj * 2
    if isinstance(obj, str):
        return f"{obj}_mod"
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise ValueError(f"Unknown leaf type: {type(obj)}")
