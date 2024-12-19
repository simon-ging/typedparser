import pytest
from typedparser.objects import (
    flatten_dict,
    invert_dict_of_dict,
    invert_list_of_dict,
)

def test_flatten_dict():
    input_dict = {'a': 1, 'b': {'c': 2, 'd': 3}}
    expected_output = {'a': 1, 'b/c': 2, 'b/d': 3}
    assert flatten_dict(input_dict) == expected_output

def test_invert_dict_of_dict():
    input_dict = {'a': {'x': 1, 'y': 2}, 'b': {'x': 3, 'y': 4}}
    expected_output = {'x': {'a': 1, 'b': 3}, 'y': {'a': 2, 'b': 4}}
    assert invert_dict_of_dict(input_dict) == expected_output

def test_invert_list_of_dict():
    input_list = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
    expected_output = {'a': [1, 3], 'b': [2, 4]}
    assert invert_list_of_dict(input_list) == expected_output
