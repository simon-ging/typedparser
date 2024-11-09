from __future__ import annotations

from typing import Dict

import pytest
from attr import define

from typedparser import attrs_from_dict


@define
class DictStrAnyCfg:
    hparams: Dict[str, any] = None


def test_dict_str_any_success():
    dct_in = {"hparams": {"lr": 1e-4}}
    attrs_obj = attrs_from_dict(DictStrAnyCfg, dct_in)
    print(attrs_obj)


@define
class DictStrStrCfg:
    hparams: Dict[str, str] = None


def test_dict_str_str_wrong_value():
    dct_in = {"hparams": {"lr": 1e-4}}  # thou shall not pass
    with pytest.raises(TypeError):
        attrs_from_dict(DictStrStrCfg, dct_in)


def test_dict_str_str_wrong_key():
    dct_in = {"hparams": {7: "a"}}  # thou shall not pass
    with pytest.raises(TypeError):
        attrs_from_dict(DictStrStrCfg, dct_in)
