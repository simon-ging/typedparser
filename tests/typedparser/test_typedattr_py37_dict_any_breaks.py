"""
One would expect this to work, but it doesn't. The `dict[str, any]` type hint is not supported
in Python 3.7 typing.get_type_hints function, even though the __future__ annotations import is used.
"""
from __future__ import annotations

import sys
from typing import get_type_hints

import pytest
from attr import define


@define
class DictStrAnyCfg:
    hparams: dict[str, any] = None


# if sys.version_info <= (3, 8):

def test_dict_any_breaks():
    # with pytest.raises(TypeError):
    print(get_type_hints(DictStrAnyCfg))
