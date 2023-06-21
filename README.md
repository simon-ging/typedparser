# typedparser

<p align="center">
<a href="https://github.com/gingsi/typedparser/actions/workflows/build_py37.yml">
  <img alt="build 3.7 status" title="build 3.7 status" src="https://img.shields.io/github/actions/workflow/status/gingsi/typedparser/build_py37.yml?branch=main&label=build%203.7" />
</a>
<a href="https://github.com/gingsi/typedparser/actions/workflows/build_py39.yml">
  <img alt="build 3.9 status" title="build 3.9 status" src="https://img.shields.io/github/actions/workflow/status/gingsi/typedparser/build_py39.yml?branch=main&label=build%203.9" />
</a>
<img alt="coverage" title="coverage" src="https://raw.githubusercontent.com/gingsi/typedparser/main/docs/coverage.svg" />
<a href="https://pypi.org/project/typedparser/">
  <img alt="version" title="version" src="https://img.shields.io/pypi/v/typedparser?color=success" />
</a>
</p>

Typing extension for python argparse using [attrs](https://www.attrs.org/en/stable/)
Includes typechecking and conversion utilities to parse a dictionary into an attrs instance. 

## Features

* Create commandline arguments with type hints and checks while
staying very close to the syntax of the standard library's argparse.
* Utilities for typechecking and converting nested objects:
  * Nested checking and conversion of python standard types
  * Supports old and new style typing (e.g. `typing.List` and `list`)
  * Supports positional and keyword arguments in classes
  * Can also typecheck existing attrs instances
  * Allows custom conversions, by default converts source type `str` to target type `Path` and
    `int` to `float`
  * Allows to redefine which objects will be recursed into, by default recurses into standard
    containers (list, dict, etc.)
  * `@definenumpy` decorator for equality check if the instances contains numpy arrays
* Some object utilities in `typedparser.objects` required for everything else

## Install

Requires `python>=3.7`

```bash
pip install typedparser
```

## Usage of the parser

1. Create an attrs class (decorate with `@attr.define`)
2. Define the fields with `typedparser.add_argument` - the syntax extends [add_argument from argparse](https://docs.python.org/3/library/argparse.html#the-add-argument-method).
3. Parse the args with `TypedParser`, now the args are typechecked and there are typehints available.  

~~~python
from typing import Optional
from attrs import define
from typedparser import add_argument, TypedParser


@define
class Args:
    foo: int = add_argument("foo", type=int)
    bar: int = add_argument("-b", "--bar", type=int, default=0)
    
    # Syntax extensions:
    
    # Omit argument name to create an optional argument --opt
    opt: Optional[int] = add_argument(type=int)
    
    # Use shortcut to create an optional argument -s / --short 
    short: Optional[int] = add_argument(shortcut="-s", type=int)


def main():
    parser = TypedParser.create_parser(Args)
    args: Args = parser.parse_args()
    print(args)


if __name__ == "__main__":
    main()

~~~

### Advanced usage

* Use `TypedParser.from_parser(parser, Args)` to add typing to an existing parser. This is useful
to cover usecases like subparsers or argument groups.

## Usage of attr utilities

Define the class hierarchy and parse the input using `attrs_from_dict`:

~~~python
from attrs import define
from typing import Optional
from typedparser import attrs_from_dict

@define
class Cfg:
    foo: int = 12
    bar: Optional[int] = None

print(attrs_from_dict(Cfg, {"foo": 1, "bar": 2}))
# Cfg(foo=1, bar=2)


@define
class CfgNested:
    sub_cfg: Cfg = None

print(attrs_from_dict(CfgNested, {"sub_cfg": {"foo": 1, "bar": 2}}))
# CfgNested(sub_cfg=Cfg(foo=1, bar=2))
~~~


### Strict mode (default)

* Convert everything to the target type, e.g. if the input is a list and the annotation is a tuple,
  the output will be a tuple
* Raise errors if types cannot be matched, there are unknown fields in the input or
  abstract annotation types are used (e.g. Sequence)

### Non-strict mode

Enabled by calling `attrs_from_dict` with `strict=False`

* No conversion except for creating the attrs instance from the dict
* Ignore silently if types cannot be matched or abstract annotation types are used
* Unknown fields in the input will be added to the attrs instance if possible
  (see the hint below about slots)

### Skip unknowns

Set `skip_unknowns=True` to ignore all unknown input fields.

### Hints

The following behaviour stems from the `attrs` package:

* New attributes cannot to be added after class definition to an attrs instance,
  unless it is created with `@define(slots=False)`
  [Explanation](https://www.attrs.org/en/21.2.0/glossary.html#term-slotted-classes)
* Untyped fields or "ClassVar" typed fields will be ignored by @attrs.define
  and therefore also by this library.

### Other utilities in the package 

* `Const`: An alternative to `enum.Enum` for defining constants
* `cacheutils`: Cache objects to disk / to memory
* `objutils`: Various utilities like nested modification of dicts
* Type definitions and other utilities


## Install locally and run tests

Clone repository and cd into, then:

~~~bash
pip install -e .
pip install pytest pytest-cov pylint pytest-lazy-fixture
pylint typedparser

# run tests for python>=3.7
python -m pytest --cov
pylint tests

# run tests for python>=3.9
python -m pytest tests tests_py39 --cov
pylint tests 
pylint tests_py39
~~~
