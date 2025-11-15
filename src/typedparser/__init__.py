from ._typedattr import NamedTupleMixin, attrs_from_dict, definenumpy
from ._typedparser import (
    TaskSplitterArgs,
    TypedParser,
    VerboseQuietArgs,
    add_argument,
    split_list_for_processing,
    split_list_given_task_splitter_args,
)
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
    "TaskSplitterArgs",
    "split_list_given_task_splitter_args",
    "split_list_for_processing",
]


__version__ = "0.33.2"
