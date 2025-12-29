import argparse
from dataclasses import dataclass
from typing import Any, Optional, Type

from attr import define, field

from .custom_format import CustomArgparseFmt
from .funcs import add_typed_args, parse_typed_args
from .objects import get_attr_names
from .typedattr import AttrsClass, NamedTupleMixin, attrs_from_dict, definenumpy

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

__version__ = "0.33.13"


@dataclass
class TypedParser:
    parser: argparse.ArgumentParser
    typed_args_class: Any
    strict: bool = False

    def __post_init__(self):
        add_typed_args(self.parser, self.typed_args_class)

    @classmethod
    def create_parser(
        cls,
        typed_args_class: AttrsClass,
        strict: bool = True,
        description: Optional[str] = None,
        formatter_class: Type = CustomArgparseFmt,
        **kwargs,
    ):
        parser = argparse.ArgumentParser(
            description=description, formatter_class=formatter_class, **kwargs
        )
        return cls(parser, typed_args_class, strict=strict)

    @classmethod
    def from_parser(
        cls, parser: argparse.ArgumentParser, typed_args_class: Any, strict: bool = False
    ):
        return cls(parser, typed_args_class, strict=strict)

    def parse_args(self, args=None, namespace=None) -> Any:
        args = self.parser.parse_args(args, namespace)
        typed_args = self._convert_args_to_typed_args(args)
        return typed_args

    def parse_known_args(self, args=None, namespace=None):
        args, unknown_args = self.parser.parse_known_args(args, namespace)
        typed_args = self._convert_args_to_typed_args(args)
        return typed_args, unknown_args

    def _convert_args_to_typed_args(self, args):
        typed_args = parse_typed_args(args, self.typed_args_class, strict=self.strict)
        return typed_args


def add_argument(
    *name_or_flags: str, shortcut: Optional[str] = None, positional: bool = False, **kwargs
) -> Any:
    """
    Interface matches ArgumentParser.add_argument:
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument

    Args:
        *name_or_flags: If not given, argument will become "--dataclass_attribute_name".
            If given, must be either a name or a list of names, e.g. "foo" or "-f", "--foo".
        shortcut: Shortcut for the argument including leading single dash.
            If given, will be added as a shortcut to the argument.
            Cannot be used if name_or_flags are given.
        positional: If True, will be added as a positional argument.
        **kwargs: will be passed to argparse parser.add_argument
    """
    assert "name_or_flags" not in kwargs, "Pass name_or_flags as positional arguments"
    if shortcut is not None:
        assert shortcut.startswith("-"), f"Shortcut {shortcut} must start with '-'"
        assert not shortcut.startswith("--"), f"Shortcut {shortcut} must not start with '--'"
    # determine the default value
    default = kwargs.get("default")
    action = kwargs.get("action")
    if default is None:
        if action is not None:
            if action == "store_true":
                default = False
            elif action == "store_false":
                default = True
            elif action == "store_const":
                default = kwargs.get("const")
            # other actions are assumed to have default None output in argparse

    return field(
        metadata={
            "name_or_flags": name_or_flags,
            "shortcut": shortcut,
            "positional": positional,
            **kwargs,
        },
        kw_only=True,
        default=default,
    )


@define(slots=False)  # slots false to allow multi inheritance
class VerboseQuietArgs:
    verbose: bool = add_argument(shortcut="-v", help="Increase verbosity", action="store_true")
    quiet: bool = add_argument(shortcut="-q", help="Reduce verbosity", action="store_true")
    loglevel: Optional[str] = add_argument(
        type=str, help="Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )


@define(slots=False)  # slots false to allow multi inheritance
class TaskSplitterArgs:
    start: int = add_argument(shortcut="-s", type=int, default=0, help="Where to start processing")
    num: Optional[int] = add_argument(shortcut="-n", type=int, help="Number of tasks to process.")


def split_list_given_task_splitter_args(
    in_list, task_splitter_args: TaskSplitterArgs, print_fn=None
):
    start, num = task_splitter_args.start, task_splitter_args.num
    return split_list_for_processing(in_list, start, num, print_fn=print_fn)


def split_list_for_processing(in_list, start: int = 0, num: Optional[int] = None, print_fn=None):
    len_in_list = len(in_list)
    if start > 0:
        in_list = in_list[start:]
    if num is not None:
        in_list = in_list[:num]
    if print_fn is not None:
        print_fn(
            f"Split list for processing, input length {len_in_list}, starting at {start}, "
            f"processing max {num} reduced to {len(in_list)}"
        )
    return in_list


