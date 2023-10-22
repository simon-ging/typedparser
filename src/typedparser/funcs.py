import argparse
from typing import Any, Dict

from attr import AttrsInstance
from attrs import has, fields_dict

from ._typedattr import attrs_from_dict
from .objects import get_attr_names


def add_typed_args(parser: argparse.ArgumentParser, typed_args_class) -> None:
    """
    Add the arguments to the parser given the types.

    Args:
        parser: the argparser
        typed_args_class: a class decorated with @attrs.define where the arguments are stored
            as fields with typedparser.add_argument().
    """
    assert isinstance(
        parser, argparse.ArgumentParser
    ), f"'{parser}' is not an argparse.ArgumentParser"
    assert has(
        typed_args_class
    ), f"'{typed_args_class}' is not an attrs class. Decorate with @typedargs"

    defargs = fields_dict(typed_args_class)
    all_names = list(defargs.keys())

    try:
        all_annotations = typed_args_class.__annotations__
    except AttributeError:
        all_annotations = {}
    unused_annotations = sorted(set(all_annotations.keys()) - set(all_names))
    assert len(unused_annotations) == 0, (
        f"Found annotations which were not parsed as attrs field. "
        f"Missing decorating @attr.define when defining the arguments? Annotations received: "
        f"{unused_annotations}"
    )

    for field_name, att in defargs.items():
        field_metadata = dict(att.metadata)

        name_or_flags = field_metadata.pop("name_or_flags", None)
        if name_or_flags is None:
            # this is a field that was not added using add_arg, ignore it
            continue

        shortcut = field_metadata.pop("shortcut", None)
        if len(name_or_flags) == 0:
            name_or_flags = []
            if shortcut is not None:
                name_or_flags.append(shortcut)
            name_or_flags.append(f"--{field_name}")
        try:
            parser.add_argument(*name_or_flags, **field_metadata)
        except TypeError as e:
            raise TypeError(
                f"Error adding argument {field_name} to parser, maybe passed keyword argument "
                f"that is incompatible with parser.add_arguments(). "
                f"Original error was {type(e).__name__}: {e}"
            ) from e
        except argparse.ArgumentError as e:
            raise ValueError(
                f"In case of conflicting option strings, make sure to not create a TypedParser "
                f"twice with the same argparser ArgumentParser. "
                f"Original error was {type(e).__name__}: {e}"
            ) from e


def parse_typed_args(
    args: argparse.Namespace, typed_args_class, strict: bool = True
) -> AttrsInstance:
    """
    Given output arguments of argparse, create a typed instance of the args class.

    Args:
        args: output arguments from argparse
        typed_args_class: a class decorated with @attrs.define where the arguments are stored
            as fields with typedparser.add_argument().
        strict: if True, typechecker will raise errors

    Returns:
        instance of typed_args_class with the fields set by the input arguments
    """
    args_dict = vars(args)
    fields_keys = list(fields_dict(typed_args_class).keys())

    missing_args = set(args_dict.keys()) - set(fields_keys)

    # in strict mode, argparse output and defined arguments class must match
    if len(missing_args) > 0:
        args_desc = {k: args_dict[k] for k in sorted(missing_args)}
        missing_err = (
            f"Argument(s) {args_desc} missing from configuration "
            f"'{typed_args_class.__name__}' with keys {fields_keys}."
        )
        if strict:
            raise KeyError(missing_err)

    # retrieve the values from argparse output and create the typed instance
    # arguments are allowed to be missing e.g. when using subparsers
    all_keys = sorted(set(args_dict.keys()) | set(fields_keys))
    kwargs = {f: args_dict.get(f) for f in all_keys}
    out_args = attrs_from_dict(typed_args_class, kwargs, strict=strict)

    if len(missing_args) > 0:
        # in non-strict mode try to add the missing arguments to the output
        try:
            for k in missing_args:
                setattr(out_args, k, args_dict[k])
        except AttributeError as e:
            raise AttributeError(
                f"Arguments are missing from configuration and cannot be added. "
                f"Either add it to the configuration or decorate with @attrs.define(slots=False) "
                f"to allow adding unknown fields. Missing: {missing_err}"
            ) from e  # noqa
    return out_args


def check_args_for_pytest(args: AttrsInstance, gt_dict: Dict[str, Any]) -> None:
    """
    Check whether the arguments match the expected ground truth dict. Useful for tests.

    Args:
        args: output arguments from TypedParser
        gt_dict: dictionary with expected values of the arguments
    """
    arg_names = get_attr_names(type(args))  # noqa
    gt_names = gt_dict.keys()
    all_names = set(arg_names) | set(gt_names)
    for key in all_names:
        if key not in gt_dict:
            raise KeyError(f"Key {key} in args {args} but not in gt_dict {gt_dict}")
        ref_value = gt_dict[key]
        atts_value = getattr(args, key)
        assert atts_value == ref_value, (
            f"Attribute {key} has value {atts_value} ({type(atts_value).__name__}) "
            f"but should be {ref_value} ({type(ref_value).__name__})"
        )
