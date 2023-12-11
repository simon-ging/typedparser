"""
Generic utilities for python objects
"""
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping, Iterable
from copy import deepcopy
from functools import partial
from typing import Any, Callable, Type, List

import numpy as np
from attr import has, AttrsInstance
from attrs import fields

AttrsClass = Type[AttrsInstance]


def get_attr_names(cls: AttrsClass) -> List[str]:
    """Get all attribute names of an attrs class."""
    return [att.name for att in fields(cls)]  # noqa


def get_all_base_classes(klass: type) -> List[type]:
    for base in klass.__bases__:
        yield base
        yield from get_all_base_classes(base)


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
) -> Any:
    """
    Traverse a python object and apply a modifier function to all leaves.

    Args:
        d: object to modify (e.g. dict)
        modifier_fn: modifier function to apply to all leaves
        return_copy: whether to copy the object before modifying it
        parser_class: which parser to use for iterable and mapping checks

    Examples:
        >>> e_dict = {'a': 1, 'b': {'c': 2, 'd': 3}}
        >>> modify_nested_object(e_dict, lambda x: x + 1)
        {'a': 2, 'b': {'c': 3, 'd': 4}}

    Returns:

    """
    parser = parser_class()

    def _modify_nested_object(d_inner: Any, depth: int = 0) -> Any:
        recursive_fn = partial(_modify_nested_object, depth=depth + 1)
        if return_copy:
            d_inner = deepcopy(d_inner)
        if parser.is_mapping_fn(d_inner):
            for k, v in d_inner.items():
                d_inner[k] = recursive_fn(v)
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
    if isinstance(d1, np.ndarray):
        comp = np.allclose(d1, d2, rtol=rtol, atol=atol, equal_nan=equal_nan)
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


def invert_dictionary(inv_dict: dict[str, dict[str, any]]) -> dict[str, dict[str, any]]:
    """
    Invert a dictionary of dictionaries. Useful for creating dataframes.

    Args:
        inv_dict: dictionary of {key1: {field1: value1, field2: value2, ...}, ...}

    Returns:
        Dictionary of {field1: {key1: value1, key2: value2, ...}, ...}

    """
    regular_dict = {}
    for key, value_dict in inv_dict.items():
        for field, value in value_dict.items():
            if field not in regular_dict:
                regular_dict[field] = {}
            regular_dict[field][key] = value
    return regular_dict
