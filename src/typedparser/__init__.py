from attrs import define as attrs_define

from ._typedattr import definenumpy, attrs_from_dict, NamedTupleMixin
from ._typedparser import add_argument, TypedParser, VerboseQuietArgs
from .custom_format import CustomArgparseFmt
from .objects import get_attr_names

__all__ = [
    "definenumpy",
    "attrs_from_dict",
    "NamedTupleMixin",
    "add_argument",
    "TypedParser",
    "VerboseQuietArgs",
    "CustomArgparseFmt",
    "get_attr_names",
]


def define(*args, **kwargs):
    print(
        f"Importing define from typedparser is deprecated, please import from attrs directly. "
        f"This import will stop working in the future."
    )
    return attrs_define(
        *args,
        **kwargs,
    )


__version__ = "0.11.5"

