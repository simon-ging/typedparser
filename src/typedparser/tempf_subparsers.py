import argparse
from pathlib import Path
from pprint import pprint
from typing import Optional

from loguru import logger
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from typedparser import VerboseQuietArgs, add_argument, define, TypedParser


@define
class Args(VerboseQuietArgs):
    base_dir: Optional[Path] = add_argument(
        shortcut="-b", type=str, help="Source base dir", default=None
    )


def main():
    # create the top-level parser

    parser = argparse.ArgumentParser(prog="PROG")

    parser.add_argument("--foo", action="store_true", help="foo help")

    subparsers = parser.add_subparsers(help="sub-command help")

    # create the parser for the "a" command

    parser_a = subparsers.add_parser("a", help="a help")

    parser_a.add_argument("bar", type=int, help="bar help")

    # create the parser for the "b" command

    parser_b = subparsers.add_parser("b", help="b help")

    parser_b.add_argument("--baz", choices="XYZ", help="baz help")

    # parse some argument lists

    args = parser.parse_args()
    pprint(args)
    # Namespace(bar=12, foo=False)


if __name__ == "__main__":
    main()
