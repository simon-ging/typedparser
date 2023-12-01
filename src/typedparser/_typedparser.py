# from __future__ import annotations  # do not use here, it breaks everything

import argparse
from dataclasses import dataclass
from typing import Optional, Type, Any

from attr import field, define

from ._typedattr import AttrsClass
from .custom_format import CustomArgparseFmt
from .funcs import parse_typed_args, add_typed_args


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

    def parse_args(self, args=None, namespace=None):
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


def add_argument(*name_or_flags: str, shortcut: Optional[str] = None, **kwargs):
    """
    Interface matches ArgumentParser.add_argument:
    https://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument

    Args:
        *name_or_flags: If not given, argument will become "--dataclass_attribute_name".
            If given, must be either a name or a list of names, e.g. "foo" or "-f", "--foo".
        shortcut: Shortcut for the argument including leading single dash.
            If given, will be added as a shortcut to the argument.
            Cannot be used if name_or_flags are given.
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
        metadata={"name_or_flags": name_or_flags, "shortcut": shortcut, **kwargs},
        kw_only=True,
        default=default,
    )


@define(slots=False)  # slots false to allow multi inheritance
class VerboseQuietArgs:
    verbose: bool = add_argument(shortcut="-v", help="Increase verbosity", action="store_true")
    quiet: bool = add_argument(shortcut="-q", help="Reduce verbosity", action="store_true")
