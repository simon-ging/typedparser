"""
Duplicate of test_typedparser.py with added future annotations
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import argparse
from copy import deepcopy
from typing import List, Optional

import pytest
from attrs import define

from typedparser import TypedParser, add_argument
from typedparser.funcs import check_args_for_pytest, parse_typed_args

# ********** Test for TypedParser **********

testdata1 = []  # config_class,inputs,outputs,strict,expected_error
testids1 = []


@define
class arg_config1:
    str_arg: str = add_argument(default=f"some_value", type=str, help="String argument")
    opt_str_arg: Optional[str] = add_argument(default=None, type=str, help="Optional argument")
    bool_arg: bool = add_argument(shortcut="-b", action="store_true")
    pos_arg: int = add_argument("pos_arg", type=int, help="Positional argument")
    multi_pos_arg: List[str] = add_argument("multi_pos_arg", type=str, nargs="+")
    default_arg: str = add_argument(default="defaultvalue", type=str, help="Default argument")


inputs1 = ("--str_arg", "some_other_value", "-b", "1", "a", "b")
outputs1 = {
    "str_arg": "some_other_value",
    "opt_str_arg": None,
    "bool_arg": True,
    "pos_arg": 1,
    "multi_pos_arg": ["a", "b"],
    "default_arg": "defaultvalue",
}
testdata1 += [
    (arg_config1, inputs1, outputs1, False, None),
    (arg_config1, inputs1, outputs1, True, None),
]
testids1 += ["correct_args_nonstrict", "correct_args_strict"]


@define
class arg_config2:
    # error: default None is not compatible with type str
    opt_str_arg: str = add_argument(default=None, type=str)


inputs2 = []
outputs2 = {
    "opt_str_arg": None,
}
testdata1 += [
    (arg_config2, inputs2, outputs2, False, None),
    (arg_config2, inputs2, outputs2, True, TypeError),
]
testids1 += ["incorrect_args_nonstrict", "incorrect_args_strict"]


@define
class arg_config3:
    opt_str_arg = add_argument(default="content", type=str)


inputs3 = []
outputs3 = {"opt_str_arg": "content"}
testdata1 += [
    (arg_config3, inputs3, outputs3, False, None),
    (arg_config3, inputs3, outputs3, True, TypeError),
]
testids1 += ["untyped_args_nonstrict", "untyped_args_strict"]


@define
class arg_config4:
    untyped_arg = add_argument(default=None, type=str)
    typed_arg: str = add_argument(default=None, type=str)


inputs4 = []
outputs4 = {
    "untyped_arg": None,
    "typed_arg": None,
}
testdata1 += [
    (arg_config4, inputs4, outputs4, False, None),
    (arg_config4, inputs4, outputs4, True, TypeError),
]
testids1 += ["partially_typed_args_nonstrict", "partially_typed_args_strict"]


@define
class arg_config5:
    str_arg: str = add_argument(type=str, positional=True)


inputs5 = ["some_other_value"]
outputs5 = {"str_arg": "some_other_value"}
testdata1 += [
    (arg_config5, inputs5, outputs5, False, None),
    (arg_config5, inputs5, outputs5, True, None),
]
testids1 += ["positional_args_nonstrict", "positional_args_strict"]


@pytest.mark.parametrize(
    "config_class,inputs,outputs,strict,expected_error", testdata1, ids=testids1
)
def test_typedparser(config_class, inputs, outputs, strict, expected_error):
    """Tests parsing of arguments with TypedParser"""
    print("*" * 80)
    print(f"class: {config_class}")
    print(f"inputs: {inputs}")
    print(f"outputs: {outputs}")
    print(f"strict: {strict}")
    parser = TypedParser.create_parser(config_class, strict=strict)
    if expected_error is not None:
        with pytest.raises(expected_error):
            parser.parse_args(inputs)
        return
    args: config_class = parser.parse_args(inputs)
    print(f"Output args: {args}")
    check_args_for_pytest(args, outputs)


# ********** Test for parse_typed_args **********


def get_typecheck_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--foo", action="store_true")
    group.add_argument("--bar", action="store_false")
    args = parser.parse_args(["--foo"])
    return args


testdata2 = []  # config_class,inputs,outputs,strict,expected_error
testids2 = []


@define
class arg_config6:
    foo: bool = None
    bar: bool = None


input_fn6 = get_typecheck_args
outputs6 = {"foo": True, "bar": True}

testdata2 += [
    (arg_config6, input_fn6, outputs6, False, None),
    (arg_config6, input_fn6, outputs6, True, None),
]
testids2 += ["correct_typecheck_nonstrict", "correct_typecheck_strict"]


@define
class arg_config7:
    foo: bool = None
    # error: missing type annotation for 'bar', crashes both strict False and True


input_fn7 = get_typecheck_args
outputs7 = {"foo": True, "bar": True}
testdata2 += [
    (arg_config7, input_fn7, outputs7, False, AttributeError),
    (arg_config7, input_fn7, outputs7, True, KeyError),
]
testids2 += ["incorrect_typecheck_nonstrict", "incorrect_typecheck_strict"]


@define(slots=False)
class arg_config8:
    foo: bool = None
    # error: missing type annotation for 'bar', slots is False so works with strict False


input_fn8 = get_typecheck_args
outputs8 = {"foo": True, "bar": True}
testdata2 += [
    (arg_config8, input_fn8, outputs8, False, None),
    (arg_config8, input_fn8, outputs8, True, KeyError),
]
testids2 += [
    "incorrect_typecheck_without_slots_nonstrict",
    "incorrect_typecheck_without_slots_strict",
]


@pytest.mark.parametrize(
    "config_class,input_fn,outputs,strict,expected_error", testdata2, ids=testids2
)
def test_typecheck(config_class, input_fn, outputs, strict, expected_error):
    """Tests only typechecking of argparse output"""
    args = input_fn()
    if expected_error is not None:
        with pytest.raises(expected_error):
            parse_typed_args(args, config_class, strict=strict)
        return
    typed_args: config_class = parse_typed_args(args, config_class, strict=strict)
    check_args_for_pytest(typed_args, outputs)


# ********** Other tests **********


@define
class arg_config9:
    bool_arg: bool = add_argument(shortcut="-b", action="store_true")
    foo: bool = None
    bar: int = None


def test_mix_argparse_and_typedparser():
    # check error on attribute missing

    # manually add some arguments
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--foo", action="store_true")
    group.add_argument("--bar", action="store_false")

    # create typed parser
    t_parser = TypedParser(deepcopy(parser), arg_config9, strict=True)
    args = t_parser.parse_args(["-b", "--bar"])
    check_args_for_pytest(args, {"bool_arg": True, "foo": False, "bar": False})


@define
class arg_config10:
    verbose: Optional[int] = add_argument(shortcut="-v", action="count")
    start10: int = add_argument(shortcut="-s", action="count", default=10)


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"verbose": None, "start10": 10}),
        (["-vv"], {"verbose": 2, "start10": 10}),
        (["-s"], {"verbose": None, "start10": 11}),
        (["-s", "-s"], {"verbose": None, "start10": 12}),
        (["-s", "-s", "-v"], {"verbose": 1, "start10": 12}),
    ),
)
def test_action_count(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config10, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config11:
    foo: Optional[int] = add_argument(action="store_const", const=42)


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": None}),
        (["--foo"], {"foo": 42}),
    ),
)
def test_action_store_const(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config11, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config12:
    foo: Optional[List[str]] = add_argument(nargs="+")


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": None}),
        (["--foo", "a", "b"], {"foo": ["a", "b"]}),
    ),
)
def test_nargs(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config12, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config13:
    foo: Optional[List[str]] = add_argument(action="append")


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": None}),
        (["--foo", "a", "--foo", "b"], {"foo": ["a", "b"]}),
    ),
)
def test_action_append(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config13, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config14:
    foo: Optional[List[str]] = add_argument(action="append_const", const="a")


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": None}),
        (["--foo", "--foo"], {"foo": ["a", "a"]}),
    ),
)
def test_action_append_const(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config14, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config15:
    bar: str = add_argument("--foo", dest="bar", default="b")


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"bar": "b"}),
        (["--foo", "a"], {"bar": "a"}),
    ),
)
def test_dest(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config15, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config16:
    foo: bool = None
    bar: Optional[int] = None
    baz: Optional[str] = None


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": False, "bar": None, "baz": None}),
        (["a", "12"], {"foo": False, "bar": 12, "baz": None}),
        (["--foo", "b", "--baz", "Z"], {"foo": True, "bar": None, "baz": "Z"}),
    ),
)
def test_subparser(args_input, gt_dict):
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

    args = TypedParser.from_parser(parser, arg_config16, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)
