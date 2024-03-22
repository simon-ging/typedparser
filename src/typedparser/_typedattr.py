from __future__ import annotations

import collections
from functools import partial
from inspect import isclass
from pathlib import Path
from typing import (
    Tuple,
    Union,
    Dict,
    AbstractSet,
    Iterable,
    Mapping,
    Collection,
    Type,
    Any,
    List,
    Optional,
    get_type_hints,
    Callable,
)

import attrs
from attr import has, AttrsInstance
from attrs import define, fields_dict, fields, Attribute

from .objects import check_object_equality, RecursorInterface, StrictRecursor, AttrsClass

try:
    from types import UnionType
except ImportError:
    UnionType = None

try:
    # python>=3.8
    from typing import get_origin, get_args
except ImportError:
    # python<3.8
    # note that attrs automatically installs this and importlib-metadata for old python versions
    from typing_extensions import get_origin, get_args

# default conversions allow to convert instead of raising errors in case of matching types
# e.g. create Path given str, or create float given int
# syntax: ((source_type1, source_type2, ...), target_type, conversion_function)
# if conversion_function is none, use target_type as conversion function
conversion_type = List[Tuple[Tuple[Type, ...], Type, Optional[Callable]]]
default_conversions: conversion_type = [
    ((str,), Path, None),
    ((int,), float, None),
    ((Path,), str, Path.as_posix),
]


def _print_fn(*args, **kwargs):  # pylint: disable=unused-argument  # noqa
    # print(*args, **kwargs)  # uncomment for debugging
    pass


def definenumpy(maybe_cls: Union[bool, Type] = False, **kwargs):
    """
    @attrs.define decorator with added numpy equality check
    """
    if isclass(maybe_cls):
        # decorator was used without brackets: call it one more time with brackets
        return definenumpy()(maybe_cls)

    frozen = maybe_cls

    def wrap(cls):
        attrs_cls = define(frozen=frozen, eq=False, **kwargs)(cls)
        attrs_cls.__eq__ = check_object_equality
        return attrs_cls

    return wrap


class NamedTupleMixin:
    """
    Make an attrs class behave more like a named tuple.

    Example:

    @define
    class FileProperties(NamedTupleMixin):
        size: int
        mtime: float
    """

    def __iter__(self):
        return (getattr(self, att.name) for att in fields(type(self)))

    def __getitem__(self, index_or_slice: int):
        return tuple(self)[index_or_slice]

    def __len__(self) -> int:
        return len(fields(type(self)))


def attrs_from_dict(
    cls: AttrsClass,
    input_dict_or_attrs_inst: Union[Dict, AttrsInstance],
    strict: bool = True,
    skip_unknowns: bool = False,
    recursor_class: Type[RecursorInterface] = StrictRecursor,
    conversions: Optional[conversion_type] = None,
) -> AttrsInstance:
    """
    Create typechecked attrs instance from dictionary or existing attrs instance.

    Args:
        cls: class decorated with @attrs.define or @definetyped
        input_dict_or_attrs_inst: data source, dict or attrs instance.
        strict: whether to do type checking and conversion
        skip_unknowns: whether to skip input fields that are not defined in cls
        recursor_class: recursor definition to find nested content
        conversions: custom conversions, e.g. if target is annotated as Path and value
            is given as str, then convert to Path instead of raising a TypeError.
            default converts int to float and str to Path.
            pass empty list to disable all conversions.

    Returns:
        Instance of cls with values from input_dict_or_attrs_inst
    """
    recursor = recursor_class()
    return _attrs_from_dict(
        recursor,
        cls,
        input_dict_or_attrs_inst,
        strict=strict,
        skip_unknowns=skip_unknowns,
        conversions=conversions,
        more_error_info=f"Parsing class {cls} from input {input_dict_or_attrs_inst}",
    )


def _attrs_from_dict(
    recursor: RecursorInterface,
    cls: AttrsClass,
    input_dict_or_attrs: Union[Dict, object],
    strict: bool = False,
    skip_unknowns: bool = False,
    conversions: Optional[conversion_type] = None,
    more_error_info: str = "",
    current_position: Optional[List] = None,
):
    if current_position is None:
        current_position = []
    _print_fn(f"Parsing {cls} from {input_dict_or_attrs}")
    input_cls = type(input_dict_or_attrs)
    if has(input_cls):
        # if given an attrs instance, convert it to dict and then
        # parse it for conversions and typechecking
        input_fields_dict = fields_dict(type(input_dict_or_attrs))
        input_dict: Dict[str, Any] = {k: getattr(input_dict_or_attrs, k) for k in input_fields_dict}
        return _attrs_from_dict(
            recursor,
            input_cls,
            input_dict,
            strict=strict,
            skip_unknowns=skip_unknowns,
            conversions=conversions,
            more_error_info=more_error_info,
        )

    input_dict: Dict[str, Any] = input_dict_or_attrs
    if input_dict is None:
        if strict:
            raise TypeError(f"Cannot parse None into {cls}")
        return None

    # check whether input and class match
    all_atts: Tuple[Attribute] = fields(cls)
    all_att_names = set(att.name for att in all_atts)
    matching_input, nonmatching_input = {}, {}
    for key, value in input_dict.items():
        if key in all_att_names:
            matching_input[key] = value
        else:
            nonmatching_input[key] = value

    # split into positional and keyword arguments
    in_args, in_kwargs = [], {}
    cls_fields_dict = fields_dict(cls)
    for field_name, field_value in matching_input.items():
        field_att = cls_fields_dict[field_name]
        try:
            is_positional = bool(field_att.default == attrs.NOTHING) and not field_att.kw_only
        except ValueError:
            # some field defaults, e.g. numpy arrays do not have comparison defined here
            # but that means that the default is set and the field is not positional
            is_positional = False
        if is_positional:
            in_args.append(field_value)
        else:
            in_kwargs[field_name] = field_value

    # create an attrs instance from the dict
    # the instance will be flat (nested dicts are not resolved yet) and not typechecked.
    try:
        cls_inst = cls(*in_args, **in_kwargs)  # noqa
        attrs_inst = cls_inst
        # # not sure why evolve was used before
        # attrs_inst = attrs.evolve(cls_inst, **in_kwargs)  # noqa
    except TypeError as e:
        raise TypeError(
            f"Failed creating instance of {cls} from input {input_dict} "
            f"with args {in_args} and kwargs {in_kwargs}. Error occurred at: "
            f"{'.'.join(current_position)}. {e}\n\nError context: {more_error_info}."
        ) from e

    # typecheck and unfold nested values in the attrs instance
    try:
        type_hints = get_type_hints(cls)
    except TypeError as e:
        raise TypeError(
            f"Failed getting type hints for {cls} with input '{input_dict}'. Error occurred at: "
            f"{'.'.join(current_position)}. {e}\n\nError context: {more_error_info}."
            "Potential reasons: You used an old python version <=3.8, used from __future__ "
            "import annotations, and annotated something as dict[str, int]. "
            "This does not work together with get_type_hints. Solution: "
            "Annotate with typing.Dict[str, int] instead of dict[str, int], or upgrade python."
        ) from e
    for att in all_atts:
        name = att.name
        value = getattr(attrs_inst, name)
        typ = att.type
        if isinstance(typ, str):
            typ = type_hints[name]

        new_value = _parse_nested(
            recursor,
            name,
            value,
            typ,
            strict=strict,
            skip_unknowns=skip_unknowns,
            conversions=conversions,
            more_error_info=more_error_info,
            current_position=current_position + [name],
        )
        setattr(attrs_inst, name, new_value)

    # handle unknown fields
    if len(nonmatching_input) > 0 and not skip_unknowns:
        if strict and not getattr(cls, "_allow_extra_keys", False):
            raise TypeError(
                f"Keys in input {list(nonmatching_input.keys())} not defined "
                f"for class {cls} with attributes {sorted(all_att_names)}"
            )
        for key, value in nonmatching_input.items():
            if skip_unknowns:
                break
            # non-strict mode and keep unknowns: try to add it to the class
            try:
                setattr(attrs_inst, key, value)
            except AttributeError as e:
                raise AttributeError(
                    f"Field {key} is missing from configuration {cls}. Either add it to the "
                    f"configuration or decorate with @attrs.define(slots=False) to allow adding "
                    f"unknown fields or set skip_unknowns=True to ignore them."
                ) from e

    _print_fn(f"Output of _attrs_from_dict: {attrs_inst}")
    return attrs_inst


def _parse_nested(
    recursor: RecursorInterface,
    name,
    value,
    typ,
    strict: bool = True,
    skip_unknowns: bool = False,
    conversions: conversion_type = None,
    depth: int = 0,
    more_error_info: str = "",
    current_position: Optional[List] = None,
):
    conversions = default_conversions if conversions is None else conversions
    parse_recursive = partial(
        _parse_nested,
        recursor,
        skip_unknowns=skip_unknowns,
        conversions=conversions,
        depth=depth + 1,
        more_error_info=more_error_info,
        current_position=current_position,
    )

    if isinstance(typ, str):
        print(f"Resolving {typ}")
        try:
            typ = get_type_hints(typ, globalns=globals())
            print(f"Resolved via get_type_hints: {typ}")
        except TypeError:
            typ = eval(typ)
            print(f"Resolved via eval: {typ}")

    origin = get_origin(typ)
    args = get_args(typ)

    target_type_name = typ.__name__ if hasattr(typ, "__name__") else str(typ)
    value_type = type(value)
    value_type_name = value_type.__name__ if hasattr(value_type, "__name__") else str(value_type)
    err_msg = (
        f"Could not parse {name}={value} (type {value_type_name}) as type "
        f"{target_type_name} with strict={strict}"
        # f" depth={depth} type annotation origin={origin} args={args}"
    )

    def maybe_raise_typeerror(full_err_msg):
        if strict:
            raise TypeError(full_err_msg)
        _print_fn(f"Caught: {full_err_msg}. Returning as is.")
        return value

    # resolve nested attrclass
    if has(typ):
        return _attrs_from_dict(
            recursor,
            typ,
            value,
            strict=strict,
            skip_unknowns=skip_unknowns,
            conversions=conversions,
            more_error_info=more_error_info,
            current_position=current_position,
        )

    # resolve any
    if typ in [Any, any]:
        return value

    # resolve unions (mostly "optional")
    if origin == Union or (UnionType is not None and isinstance(typ, UnionType)):
        collected_errors = []
        for new_typ in args:
            try:
                # force strict parsing and catch errors to try all different types
                return parse_recursive(name, value, new_typ, strict=True)
            except TypeError as e:
                collected_errors.append(f"{e}")
        # if we get here, none of the types worked
        collected_error_str = "\n".join(collected_errors)
        return maybe_raise_typeerror(
            f"No type in Union matches. Errors per type:\n{collected_error_str}\n"
            f"Final error: {err_msg}"
        )

    final_list_type = None

    # check tuples
    if origin == tuple:
        if not (len(args) == 2 and args[1] == Ellipsis):
            # resolve fixed tuple
            if not recursor.is_iterable_fn(value):
                return maybe_raise_typeerror(f"{err_msg}. Expect a sequence, got {type(value)}")
            if len(value) != len(args):
                return maybe_raise_typeerror(
                    f"{err_msg}. Expect a sequence with length {len(args)}, got length {len(value)}"
                )
            new_tuple = []
            for item, item_type in zip(value, args):
                new_tuple.append(parse_recursive(name, item, item_type, strict=strict))
            return tuple(new_tuple)
        if len(args) == 0:
            # undefined tuple can be anything
            args = [Any, Ellipsis]

    # check dict
    if origin in (dict, collections.defaultdict):
        if not recursor.is_mapping_fn(value):
            return maybe_raise_typeerror(f"{err_msg}. Expect a mapping, got {type(value)}")
        if len(args) == 0:
            args = [Any, Any]
        dict_keytype, dict_valuetype = args

        if origin == collections.defaultdict:
            # must keep the default factory if exists
            dict_output = collections.defaultdict(getattr(value, "default_factory", None))
        else:
            dict_output = {}

        for key, val in value.items():
            parsed_key = parse_recursive(f"{name}/dict_key_type", key, dict_keytype, strict=strict)
            parsed_value = parse_recursive(f"{name}/{key}", val, dict_valuetype, strict=strict)
            dict_output[parsed_key] = parsed_value

        return dict_output

    if origin in [set, frozenset, tuple]:
        # delegate to list parser
        origin, final_list_type = list, origin
        if len(args) == 0:
            args = [Any]
        args = [args[0]]

    # resolve list
    if origin == list:
        if not recursor.is_iterable_fn(value):
            return maybe_raise_typeerror(f"{err_msg}. Expect iterable, got {type(value)}")
        list_arg_type = args[0]
        list_output = []
        for item in value:
            list_item = parse_recursive(name, item, list_arg_type, strict=strict)
            list_output.append(list_item)
        if not strict:
            # make sure to not change the input value type
            final_list_type = type(value)
        if final_list_type is not None:
            list_output = final_list_type(list_output)
        return list_output

    # try to parse as a regular type (float, etc), this also parses Callable and any other types
    # but only non-nested parsing and no further inspection.
    try:
        if isinstance(value, typ):
            return value
        _print_fn(f"Not compatible: {value} as {typ}, {err_msg}")

    except TypeError as e:
        _print_fn(f"Caught {e} while trying to parse {value} as {typ}, {err_msg}")

    # show better error message for abstract types
    try:
        is_sc = issubclass(origin, (AbstractSet, Mapping, Collection, Iterable))
    except TypeError:
        is_sc = False
    if is_sc:
        return maybe_raise_typeerror(f"{err_msg}. Abstract collections are not supported.")

    # add explicit conversions
    for convert_source, convert_target, convert_callable in conversions:
        if not isclass(typ):
            continue
        if issubclass(typ, convert_target) and isinstance(value, convert_source):
            if convert_callable is None:
                convert_callable = convert_target
            return convert_callable(value)

    if strict:
        add_info = ""
        if typ is None:
            add_info = (
                "Untyped fields not allowed in strict mode. "
                "Add type annotations or set strict=False. "
            )

        raise TypeError(f"{add_info}{err_msg}. Wrong type or type not supported.")
    _print_fn(f"{err_msg}. Returning value {value} as-is")
    return value
