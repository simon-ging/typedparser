"""
Test the pipe operator for Optional[int] type definition. (new syntax from python 3.10)
with added future annotations.
"""
# pylint: disable=unsubscriptable-object
from __future__ import annotations

from collections import defaultdict

import attrs
import sys
from attr import define
from collections.abc import Callable

from typedparser import attrs_from_dict

if sys.version_info >= (3, 10):

    @define
    class Cfg:
        f1: int = 12
        f2: int | None = None
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
        assert attrs.asdict(c) == {
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
