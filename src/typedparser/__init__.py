from ._typedattr import definenumpy, attrs_from_dict, NamedTupleMixin
from ._typedparser import add_argument, TypedParser, VerboseQuietArgs
from .custom_format import CustomArgparseFmt
from .objects import get_attr_names
from attrs import define

__all__ = [
    "definenumpy",
    "attrs_from_dict",
    "NamedTupleMixin",
    "add_argument",
    "TypedParser",
    "VerboseQuietArgs",
    "CustomArgparseFmt",
    "get_attr_names",
    "define",  # deprecated, use `from attr import define` directly instead
]
__version__ = "0.9.1"
