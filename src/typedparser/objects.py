"""
Generic utilities for python objects
"""

from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Mapping
from copy import deepcopy
from functools import partial
from typing import Any, Callable, List, Type

from attr import AttrsInstance, has
from attrs import fields

AttrsClass = Type[AttrsInstance]

try:
    import numpy as np
except ImportError:
    np = None


def get_attr_names(cls: AttrsClass) -> List[str]:
    """Get all attribute names of an attrs class."""
    return [att.name for att in fields(cls)]  # noqa


# def _get_all_base_classes_rec(klass: type) -> Generator[type, None, None]:
#     for base in klass.__bases__:
#         yield base
#         yield from _get_all_base_classes_rec(base)


def get_all_base_classes(input_class: type) -> List[type]:
    classes = {}

    def _get_all_base_classes_rec(class_here: type):
        for base in class_here.__bases__:
            if base == object:
                continue
            if base in classes:
                continue
            classes[base] = base
            _get_all_base_classes_rec(base)

    _get_all_base_classes_rec(input_class)
    return list(classes.values())


def is_standard_mapping(d: Any) -> bool:
    return isinstance(d, (dict,))


def is_standard_iterable(d: Any) -> bool:
    return isinstance(d, (list, tuple, set, frozenset))


def is_any_mapping(d: Any) -> bool:
    return isinstance(d, Mapping)


def is_any_iterable(d: Any) -> bool:
    return isinstance(d, Iterable)


def is_iterable(d: Any) -> bool:
    return isinstance(d, Iterable) and not isinstance(d, (str, bytes))


class RecursorInterface(metaclass=ABCMeta):
    @abstractmethod
    def is_iterable_fn(self, d: Any) -> bool:
        pass

    @abstractmethod
    def is_mapping_fn(self, d: Any) -> bool:
        pass


class DefaultRecursor(RecursorInterface):
    """Recurses into all iterables and mappings, except str-like objects"""

    def is_iterable_fn(self, d: Any) -> bool:
        return is_iterable(d)

    def is_mapping_fn(self, d: Any) -> bool:
        return is_any_mapping(d)


class StrictRecursor(RecursorInterface):
    """Recurses only into standard iterables and mappings"""

    def is_iterable_fn(self, d: Any) -> bool:
        return is_standard_iterable(d)

    def is_mapping_fn(self, d: Any) -> bool:
        return is_standard_mapping(d)


def modify_nested_object(
    d: Any,
    modifier_fn: Callable,
    return_copy: bool = False,
    parser_class: Type[RecursorInterface] = StrictRecursor,
    tuple_to_list: bool = False,
) -> Any:
    """
    Traverse a python object and apply a modifier function to all leaves.

    Note: This also modifies tuples and sets.

    Args:
        d: object to modify (e.g. dict)
        modifier_fn: modifier function to apply to all leaves
        return_copy: whether to copy the object before modifying it
        parser_class: which parser to use for iterable and mapping checks
        tuple_to_list: if True, convert tuples to lists

    Examples:
        >>> e_dict = {'a': 1, 'b': {'c': 2, 'd': 3}}
        >>> modify_nested_object(e_dict, lambda x: x + 1)
        {'a': 2, 'b': {'c': 3, 'd': 4}}

    Returns:

    """
    parser = parser_class()
    tuple_type = list if tuple_to_list else tuple
    if return_copy:
        d = deepcopy(d)

    def _modify_nested_object(d_inner: Any, depth: int = 0) -> Any:
        recursive_fn = partial(_modify_nested_object, depth=depth + 1)
        if parser.is_mapping_fn(d_inner):
            for k, v in d_inner.items():
                d_inner[k] = recursive_fn(v)
        elif isinstance(d_inner, tuple):  # tuple does not support in-place modification
            d_inner = tuple_type(recursive_fn(v) for v in d_inner)
        elif isinstance(d_inner, set):  # set does not support in-place modification
            d_inner = set(recursive_fn(v) for v in d_inner)
        elif parser.is_iterable_fn(d_inner):
            for i, v in enumerate(d_inner):
                d_inner[i] = recursive_fn(v)
        else:
            d_inner = modifier_fn(d_inner)
        return d_inner

    return _modify_nested_object(d)


def flatten_dict(
    d: Any,
    separator_for_dict="/",
    separator_for_list="#",
    parser_class: Type[RecursorInterface] = StrictRecursor,
):
    """
    Flatten a nested dict by joining nested keys with a separator.

    Args:
        d: dict to flatten
        separator_for_dict: separator to use for nested dict keys
        separator_for_list: separator to use for list indices
        parser_class: which parser to use for iterable and mapping checks

    Examples:
        >>> e_dict = {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': [1, 2, "6"]}
        >>> flatten_dict(e_dict)
        {'a': 1, 'b/c': 2, 'b/d': 3, 'e#0': 1, 'e#1': 2, 'e#2': '6'}

    Returns:
        Flat dict.
    """
    parser = parser_class()

    def _check_key(key_inner):
        assert separator_for_dict not in key_inner and separator_for_list not in key_inner, (
            f"Separators '{separator_for_dict}' and '{separator_for_list}' not allowed in key "
            f"'{key_inner}' when flattening dict."
        )

    def _flatten_leaf(d_inner, prefix):
        items_inner = []
        if parser.is_mapping_fn(d_inner):
            for k_inner, v_inner in d_inner.items():
                k_inner_str = str(k_inner)
                _check_key(k_inner_str)
                items_inner.extend(
                    _flatten_leaf(v_inner, prefix=f"{prefix}{separator_for_dict}{k_inner_str}")
                )
        elif parser.is_iterable_fn(d_inner):
            for i, v_inner in enumerate(d_inner):
                items_inner.extend(
                    _flatten_leaf(v_inner, prefix=f"{prefix}{separator_for_list}{i}")
                )
        else:
            items_inner.append((prefix, d_inner))
        return items_inner

    items = []
    for k, v in d.items():
        items.extend(_flatten_leaf(v, prefix=f"{k}"))
    return dict(items)


def compare_nested_objects(
    d1_outer: Any,
    d2_outer: Any,
    recursor_class: Type[RecursorInterface] = StrictRecursor,
    rtol=1.0e-5,
    atol=1.0e-8,
    equal_nan=False,
) -> List[str]:
    """
    Compare two nested objects (e.g. dicts) and return a list of str describing all differences.

    Args:
        d1_outer: object 1
        d2_outer: object 2
        recursor_class: recursor definition to find nested content
        rtol: see numpy.allclose
        atol: see numpy.allclose
        equal_nan: see numpy.allclose

    Returns:
        List of strings describing the differences between the two objects.
        Empty list means the objects are identical.
    """
    recursor = recursor_class()

    def _compare_nested_objects(d1, d2, depth: int = 0, prefix=""):
        # prefix = {' ' * depth}
        if type(d1) != type(d2):  # noqa  # pylint: disable=unidiomatic-typecheck
            return [f"{prefix} Type mismatch: {type(d1)} != {type(d2)}"]

        if isinstance(d1, str):
            # leaf - guard against infinite iteration of strings
            return _compare_leaf(d1, d2, depth, prefix=prefix)

        if recursor.is_mapping_fn(d1):
            all_errors = []
            for k, v in d1.items():
                if k not in d2:
                    all_errors.append(f"{prefix} Key {k} missing in second dict")
                    continue
                all_errors.extend(
                    _compare_nested_objects(v, d2[k], depth + 1, prefix=f"{prefix}.{k}")
                )
            for k in d2.keys():
                if k not in d1:
                    all_errors.append(f"{prefix} Key {k} missing in first dict")
            return all_errors

        if recursor.is_iterable_fn(d1):
            all_errors = []
            if len(d1) != len(d2):
                all_errors.append(f"{prefix} Length mismatch: {len(d1)} != {len(d2)}")
            else:
                for i, v in enumerate(d1):
                    all_errors.extend(
                        _compare_nested_objects(v, d2[i], depth + 1, prefix=f"{prefix}[{i}]")
                    )
            return all_errors

        if has(type(d1)):
            # exact definition of the attrs class is not important
            # attribute names and values matching is enough
            atts1 = get_attr_names(type(d1))
            atts2 = get_attr_names(type(d2))
            if atts1 != atts2:
                return [f"{prefix} Attribute names mismatch: {atts1} != {atts2}"]

            all_errors = []
            for att_name in atts1:
                # check if attributes are defined in the same way
                d1_att = getattr(d1, att_name)
                d2_att = getattr(d2, att_name)
                if type(d1_att) != type(d2_att):  # noqa  # pylint: disable=unidiomatic-typecheck
                    all_errors.append(
                        f"{prefix} Attribute {att_name} type mismatch: "
                        f"({type(d1_att)}) != ({type(d2_att)})"
                    )
                else:
                    all_errors.extend(
                        _compare_nested_objects(
                            d1_att, d2_att, depth + 1, prefix=f"{prefix}.{att_name}"
                        )
                    )
            return all_errors

        return _compare_leaf(
            d1, d2, depth, rtol=rtol, atol=atol, equal_nan=equal_nan, prefix=prefix
        )

    return _compare_nested_objects(d1_outer, d2_outer)


def _compare_leaf(
    d1: Any, d2: Any, _depth: int, rtol=1.0e-5, atol=1.0e-8, equal_nan=False, prefix=""
) -> List[str]:

    # at this point the 2 leaves are guaranteed to be the same type
    if np is not None and isinstance(d1, np.ndarray):  # noqa
        comp = np.allclose(d1, d2, rtol=rtol, atol=atol, equal_nan=equal_nan)  # noqa
    else:
        comp = d1 == d2
    if not comp:
        return [f"{prefix} {d1} != {d2}"]
    return []


def check_object_equality(
    d1: Any, d2: Any, recursor_class: Type[RecursorInterface] = StrictRecursor
) -> bool:
    """
    Compare two nested objects (e.g. dicts) and return equality as boolean.

    Args:
        d1: object 1
        d2: object 2
        recursor_class: recursor definition to find nested content

    Returns:
        List of strings describing the differences between the two objects.
        Empty list means the objects are identical.
    """
    return len(compare_nested_objects(d1, d2, recursor_class)) == 0


def big_obj_to_short_str(d: Any) -> str:
    """
    Args:
        d: any big object e.g. a dict or a numpy array

    Returns:
        A hopefully short and representative string representation of the object.
    """
    if d is None:
        return str(None)
    class_name = type(d).__name__
    if hasattr(d, "shape"):
        return f"{class_name} shape {d.shape}"
    try:
        return f"{class_name} len {len(d)}"
    except TypeError:
        return f"Object of type {class_name}"


def invert_dict_of_dict(dict_of_dict: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """
    Invert a dictionary of dictionaries. Useful for creating dataframes.

    Args:
        dict_of_dict: dictionary of {key1: {field1: value1, field2: value2, ...}, ...}

    Returns:
        Dictionary of {field1: {key1: value1, key2: value2, ...}, ...}

    """
    regular_dict = {}
    for key, value_dict in dict_of_dict.items():
        for field, value in value_dict.items():
            if field not in regular_dict:
                regular_dict[field] = {}
            regular_dict[field][key] = value
    return regular_dict


def invert_list_of_dict(list_of_dict: list[dict[str, Any]]) -> dict[str, list[Any]]:
    """
    Invert a list of dictionaries. Useful for creating dataframes.

    Args:
        list_of_dict: list of {field1: value1, field2: value2, ...}

    Returns:
        Dictionary of {field1: [value1, value2, ...], ...}

    """
    dict_of_list = {}
    for value_dict in list_of_dict:
        for field, value in value_dict.items():
            if field not in dict_of_list:
                dict_of_list[field] = []
            dict_of_list[field].append(value)
    return dict_of_list


def inspect_obj(obj) -> str:
    strs = []
    members = inspect.getmembers(obj)
    srt = defaultdict(list)
    for key, value in members:
        if key.startswith("_"):
            continue
        # print(key, type(value))
        srt[value.__class__.__name__].append(key)
    for key in sorted(srt.keys()):
        for attr in sorted(srt[key]):
            strs.append(f"{key} {attr}\n")
    return "".join(strs)


def convert_dataclass_instance_to_dict(d_instance, d_class) -> dict:
    return {k: getattr(d_instance, k) for k in d_class.__dataclass_fields__.keys()}


def analyze_flat_object(value_) -> str:
    output_strs = []
    if hasattr(value_, "shape"):
        output_strs.append(f"shape={value_.shape}")
    elif hasattr(value_, "__len__"):
        output_strs.append(f"len={len(value_)}")
    if hasattr(value_, "dtype"):
        output_strs.append(f"dtype={value_.dtype}")
    output_strs.append(get_obj_str_with_max_len(value_, max_len=50))
    return " ".join(output_strs)


def analyze_nested_object_structure(
    d: Any,
    is_iterable_fn: Callable = is_standard_iterable,
    is_mapping_fn: Callable = is_standard_mapping,
    depth: int = 0,
) -> str:
    # this assumes fixed structure objects (i.e. each item of a container has the same structure)
    pre = ""  # f" " * depth
    value_strs = []

    if is_mapping_fn(d):
        # dict-like
        for k, v in d.items():
            value_str = analyze_nested_object_structure(v, is_iterable_fn, is_mapping_fn, depth + 1)
            value_strs.append(f"{pre} dict {k} -> {value_str}")
            break
    elif is_iterable_fn(d):
        # list-like
        for i, v in enumerate(d):
            value_str = analyze_nested_object_structure(v, is_iterable_fn, is_mapping_fn, depth + 1)
            value_strs.append(f"{pre} list #{i}: {value_str}")
            break
    else:
        # leaf
        value_str = analyze_flat_object(d)
        value_strs.append(f"{pre} {value_str}")
    return "\n".join(value_strs)


def print_datapoint(dp, max_str_len=200):
    for k, v in dp.items():
        if hasattr(v, "shape"):
            v_str = f"shape={v.shape} dtype={v.dtype}"
        elif isinstance(v, (list, tuple)):
            v_str = f"len={len(v)} {v[:5]}..."
        else:
            v_str = f"class={v.__class__.__name__} {v}"
        if len(v_str) > max_str_len:
            v_str = v_str[:max_str_len] + "..."
        print(f"    {k}: {v_str}")


def print_item_recursively(item, depth=0):
    """Print information about e.g. a datapoint containing nested items of various types."""
    pre = "  " * depth
    cls = item.__class__.__name__
    if isinstance(item, dict):
        for k, v in item.items():
            print(f"{pre}{k}")
            print_item_recursively(v, depth=depth + 1)
    elif isinstance(item, (list, tuple)):
        for v in item:
            print_item_recursively(v, depth=depth + 1)
    elif hasattr(item, "shape"):
        print(f"{pre}{item.shape} ({cls})")
    else:
        print(f"{pre}{item} ({cls})")


def get_obj_str_with_max_len(obj: Any, max_len: int = 100):
    obj_str = str(obj)
    obj_str = (
        obj_str[:max_len] + f"... (total_str_len={len(obj_str)})"
        if len(obj_str) > max_len
        else obj_str
    )
    return obj_str


def _get_indent(depth, key, fmt="  "):
    indent = fmt * depth
    if key is not None:
        indent = f"{indent}{key}: "
    return indent


def repr_value(
    value, max_list_items=3, max_dict_items=8, max_str_len=200, depth=0, key=None, fmt="  "
):
    repr_value_recursor = partial(
        repr_value,
        max_list_items=max_list_items,
        max_dict_items=max_dict_items,
        max_str_len=max_str_len,
        depth=depth + 1,
        fmt=fmt,
    )
    typ = type(value).__name__
    indent = _get_indent(depth, key, fmt=fmt)
    indent_plus_1 = _get_indent(depth + 1, None, fmt=fmt)
    indent_minus_1 = _get_indent(depth - 1, None, fmt=fmt)
    if isinstance(value, str):
        value_str = value
        if len(value) > max_str_len > 0:
            value_str = "".join(
                [value[: max_str_len // 2], " ... ", value[-max_str_len // 2 - 5 :]]
            )
        return f"{indent}{typ} len={len(value)}: {value_str}"

    if isinstance(value, bytes):
        value_str = value
        if len(value) > max_str_len > 0:
            value_str = b"".join([value[:100], b" ... ", value[-95:]])
        return f"{indent}{typ} len={len(value)}: {value_str}"

    # if isinstance(value, torch.Tensor):
    if hasattr(value, "shape") and hasattr(value, "dtype"):
        return f"{indent}{typ} shape={value.shape} dtype={value.dtype}"

    if is_any_mapping(value):
        keys = list(value.keys())
        show_len = len(keys)
        if max_dict_items > 0:
            show_len = min(max_dict_items, len(keys))
        reprs = [f"{indent_minus_1}{repr_value_recursor(value[k],key=k)}" for k in keys[:show_len]]
        if show_len < len(keys):
            reprs.append("...")
        out_str = f"{indent}{typ} len={len(keys)}\n" + "\n".join(reprs)
        return out_str

    # note: handle all iterables that should not get recursed into, above this line.
    if is_any_iterable(value):
        show_len = len(value)
        if max_list_items > 0:
            show_len = min(max_list_items, len(value))
        reprs = [repr_value_recursor(v) for v in value[:show_len]]
        if show_len < len(value):
            reprs.append(f"{indent_plus_1}...")
        out_str = f"{indent}{typ} len={len(value)}\n" + "\n".join(reprs)
        return out_str

    return f"{indent}{typ}: {str(value)}"

    # if value is None:
    #     return f"{indent}{typ}: None"
    #
    # raise NotImplementedError(f"repr_value not implemented for {typ}")
