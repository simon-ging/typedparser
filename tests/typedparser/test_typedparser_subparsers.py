import argparse
from typing import Optional

import pytest
from attrs import define

from typedparser import TypedParser
from typedparser.funcs import check_args_for_pytest


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": False, "bar": None, "baz": None}),
        (["a", "12"], {"foo": False, "bar": 12, "baz": None}),
        (["--foo", "b", "--baz", "Z"], {"foo": True, "bar": None, "baz": "Z"}),
    ),
)
def test_subparser_simple(args_input, gt_dict):
    """
    Create a nested parser with argparse and use typedparser to create the final typed args
    """

    @define
    class arg_config:
        foo: bool = None
        bar: Optional[int] = None
        baz: Optional[str] = None

    # create the top-level parser
    parser = argparse.ArgumentParser(prog="PROG")
    parser.add_argument("--foo", action="store_true", help="foo help")
    subparsers = parser.add_subparsers(help="sub-command help")
    # create the parser for the "a" command
    parser_a = subparsers.add_parser("a", help="a help")
    parser_a.add_argument("bar", type=int, help="bar help", default=11)
    # create the parser for the "b" command
    parser_b = subparsers.add_parser("b", help="b help")
    parser_b.add_argument("--baz", choices="XYZ", help="baz help")

    args = TypedParser.from_parser(parser, arg_config, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)
