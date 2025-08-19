"""
Duplicate of test_typedattr_py39.py with added future annotations.
"""

# pylint: disable=duplicate-code

from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Callable
from typing import Optional

from attrs import asdict, define

from typedparser import attrs_from_dict

if sys.version_info >= (3, 9):

    @define
    class Cfg:
        f1: int = 12
        f2: Optional[int] = None
        f3: tuple[int, str] = [12, "a"]
        f4: tuple[int, ...] = [12, 13, -1]
        f5: list[int] = [12]
        f6: Callable = print
        f7: set[int] = {12}
        f8: frozenset[int] = frozenset({12})
        f9: dict[str, str] = {"a": "b", "c": "d"}
        f10: defaultdict = defaultdict(list)

    # @pytest.mark.skipif(sys.version_info < (3, 8), reason="requires python3.9 or higher")
    def test_typedattr_py39():
        c = attrs_from_dict(Cfg, {}, strict=True)
        assert asdict(c) == {
            "f1": 12,
            "f2": None,
            "f3": (12, "a"),
            "f4": (12, 13, -1),
            "f5": [12],
            "f6": print,
            "f7": {12},
            "f8": frozenset({12}),
            "f9": {"a": "b", "c": "d"},
            "f10": {},
        }

    def main():
        test_typedattr_py39()

    if __name__ == "__main__":
        main()
