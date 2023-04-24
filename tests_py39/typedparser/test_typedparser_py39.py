from typing import List, Optional

import pytest

from typedparser import add_argument, TypedParser, define
from typedparser.funcs import check_args_for_pytest


@pytest.mark.parametrize(
    "args_input, gt_dict", (
            ([], {"foo": None}),
            (["--foo", "f1", "--foo", "f2", "f3", "f4"], {"foo": ['f1', 'f2', 'f3', 'f4']}),
    ))
def test_action_extend(args_input, gt_dict):
    @define
    class arg_config:
        foo: Optional[List[str]] = add_argument(action="extend", nargs="+")


    args = TypedParser.create_parser(arg_config, strict=True).parse_args(args_input)
    check_args_for_pytest(args, gt_dict)
