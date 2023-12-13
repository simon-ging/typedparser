import argparse
from copy import deepcopy
from typing import List, Optional

import pytest
from attrs import define
from pytest_lazyfixture import lazy_fixture

from typedparser import add_argument, TypedParser
from typedparser.funcs import parse_typed_args, check_args_for_pytest


@define
class arg_config1:
    str_arg: str = add_argument(default=f"some_value", type=str, help="String argument")
    opt_str_arg: Optional[str] = add_argument(default=None, type=str, help="Optional argument")
    bool_arg: bool = add_argument(shortcut="-b", action="store_true")
    pos_arg: int = add_argument("pos_arg", type=int, help="Positional argument")
    multi_pos_arg: List[str] = add_argument("multi_pos_arg", type=str, nargs="+")
    default_arg: str = add_argument(default="defaultvalue", type=str, help="Default argument")


@pytest.fixture(scope="module", params=([False, None], [True, None]), ids=("nonstrict", "strict"))
def setup_correct_args(request):
    strict, expected_error = request.param
    inputs = ["--str_arg", "some_other_value", "-b", "1", "a", "b"]
    outputs = {
        "str_arg": "some_other_value",
        "opt_str_arg": None,
        "bool_arg": True,
        "pos_arg": 1,
        "multi_pos_arg": ["a", "b"],
        "default_arg": "defaultvalue",
    }
    yield arg_config1, inputs, outputs, strict, expected_error


@define
class arg_config2:
    # error: default None is not compatible with type str
    opt_str_arg: str = add_argument(default=None, type=str)


@pytest.fixture(
    scope="module", params=([False, None], [True, TypeError]), ids=("nonstrict", "strict")
)
def setup_incorrect_args(request):
    strict, expected_error = request.param
    inputs = []
    outputs = {
        "opt_str_arg": None,
    }
    yield arg_config2, inputs, outputs, strict, expected_error


@define
class arg_config3:
    opt_str_arg = add_argument(default="content", type=str)


@pytest.fixture(
    scope="module", params=([False, None], [True, TypeError]), ids=("nonstrict", "strict")
)
def setup_untyped_args(request):
    strict, expected_error = request.param
    inputs = []
    outputs = {"opt_str_arg": "content"}
    yield arg_config3, inputs, outputs, strict, expected_error


@define
class arg_config4:
    untyped_arg = add_argument(default=None, type=str)
    typed_arg: str = add_argument(default=None, type=str)


@pytest.fixture(
    scope="module", params=([False, None], [True, TypeError]), ids=("nonstrict", "strict")
)
def setup_partially_typed_args(request):
    strict, expected_error = request.param
    inputs = []
    outputs = {
        "untyped_arg": None,
        "typed_arg": None,
    }
    yield arg_config4, inputs, outputs, strict, expected_error


@define
class arg_config_pos:
    str_arg: str = add_argument(type=str, positional=True)


@pytest.fixture(scope="module")
def setup_positional_args(request):
    strict, expected_error = False, None
    inputs = ["some_other_value"]
    outputs = {
        "str_arg": "some_other_value",
    }
    yield arg_config_pos, inputs, outputs, strict, expected_error


# todo test shortcut and positionla wrong usage


@pytest.mark.parametrize(
    "setup_all_args",
    [
        lazy_fixture("setup_correct_args"),
        lazy_fixture("setup_incorrect_args"),
        lazy_fixture("setup_untyped_args"),
        lazy_fixture("setup_partially_typed_args"),
        lazy_fixture("setup_positional_args"),
    ],
)
def test_typedparser(setup_all_args):
    """Tests parsing of arguments with TypedParser"""
    config_class, inputs, outputs, strict, expected_error = setup_all_args
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



def get_typecheck_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--foo", action="store_true")
    group.add_argument("--bar", action="store_false")
    args = parser.parse_args(["--foo"])
    return args


@define
class arg_config5:
    foo: bool = None
    bar: bool = None


@pytest.fixture(scope="module", params=([False, None], [True, None]), ids=("nonstrict", "strict"))
def setup_correct_typecheck(request):
    strict, expected_error = request.param
    yield arg_config5, get_typecheck_args(), {"foo": True, "bar": True}, strict, expected_error


@define
class arg_config6:
    foo: bool = None
    # error: missing type annotation for 'bar', crashes both strict False and True


@pytest.fixture(
    scope="module", params=([False, AttributeError], [True, KeyError]), ids=("nonstrict", "strict")
)
def setup_incorrect_typecheck(request):
    strict, expected_error = request.param
    yield arg_config6, get_typecheck_args(), {"foo": True, "bar": True}, strict, expected_error


@define(slots=False)
class arg_config7:
    foo: bool = None
    # error: missing type annotation for 'bar', slots is False so works with strict False


@pytest.fixture(
    scope="module", params=([False, None], [True, KeyError]), ids=("nonstrict", "strict")
)
def setup_incorrect_typecheck_without_slots(request):
    strict, expected_error = request.param
    yield arg_config7, get_typecheck_args(), {"foo": True, "bar": True}, strict, expected_error


@pytest.mark.parametrize(
    "setup_all_typechecks",
    [
        lazy_fixture("setup_correct_typecheck"),
        lazy_fixture("setup_incorrect_typecheck"),
        lazy_fixture("setup_incorrect_typecheck_without_slots"),
    ],
)
def test_typecheck(setup_all_typechecks):
    """Tests only typechecking of argparse output"""
    print(f"********** {setup_all_typechecks} **********")
    config_class, args, outputs, strict, expected_error = setup_all_typechecks
    if expected_error is not None:
        with pytest.raises(expected_error):
            parse_typed_args(args, config_class, strict=strict)
        return
    typed_args: config_class = parse_typed_args(args, config_class, strict=strict)
    check_args_for_pytest(typed_args, outputs)


@define
class arg_config8:
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
    t_parser = TypedParser(deepcopy(parser), arg_config8, strict=True)
    args = t_parser.parse_args(["-b", "--bar"])
    check_args_for_pytest(args, {"bool_arg": True, "foo": False, "bar": False})


@define
class arg_config9:
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
    args = TypedParser.create_parser(arg_config9, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config10:
    foo: Optional[int] = add_argument(action="store_const", const=42)


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": None}),
        (["--foo"], {"foo": 42}),
    ),
)
def test_action_store_const(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config10, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config11:
    foo: Optional[List[str]] = add_argument(nargs="+")


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": None}),
        (["--foo", "a", "b"], {"foo": ["a", "b"]}),
    ),
)
def test_nargs(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config11, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config12:
    foo: Optional[List[str]] = add_argument(action="append")


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": None}),
        (["--foo", "a", "--foo", "b"], {"foo": ["a", "b"]}),
    ),
)
def test_action_append(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config12, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config13:
    foo: Optional[List[str]] = add_argument(action="append_const", const="a")


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"foo": None}),
        (["--foo", "--foo"], {"foo": ["a", "a"]}),
    ),
)
def test_action_append_const(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config13, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config14:
    bar: str = add_argument("--foo", dest="bar", default="b")


@pytest.mark.parametrize(
    "args_input, gt_dict",
    (
        ([], {"bar": "b"}),
        (["--foo", "a"], {"bar": "a"}),
    ),
)
def test_dest(args_input, gt_dict):
    args = TypedParser.create_parser(arg_config14, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)


@define
class arg_config15:
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

    args = TypedParser.from_parser(parser, arg_config15, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)
