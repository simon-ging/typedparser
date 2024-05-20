# typedparser

<p align="center">
<a href="https://github.com/simon-ging/typedparser/actions/workflows/build-py37.yml">
  <img alt="build 3.7 status" title="build 3.7 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/typedparser/build-py37.yml?branch=main&label=python%203.7" />
</a>
<a href="https://github.com/simon-ging/typedparser/actions/workflows/build-py38.yml">
  <img alt="build 3.8 status" title="build 3.8 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/typedparser/build-py38.yml?branch=main&label=python%203.8" />
</a>
<a href="https://github.com/simon-ging/typedparser/actions/workflows/build-py39.yml">
  <img alt="build 3.9 status" title="build 3.9 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/typedparser/build-py39.yml?branch=main&label=python%203.9" />
</a>
<a href="https://github.com/simon-ging/typedparser/actions/workflows/build-py310.yml">
  <img alt="build 3.10 status" title="build 3.10 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/typedparser/build-py310.yml?branch=main&label=python%203.10" />
</a>
<a href="https://github.com/simon-ging/typedparser/actions/workflows/build-py311.yml">
  <img alt="build 3.11 status" title="build 3.11 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/typedparser/build-py311.yml?branch=main&label=python%203.11" />
</a>
<a href="https://github.com/simon-ging/typedparser/actions/workflows/build-py312.yml">
  <img alt="build 3.12 status" title="build 3.12 status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/typedparser/build-py312.yml?branch=main&label=python%203.12" />
</a>
<a href="https://github.com/simon-ging/typedparser/actions/workflows/build-py37-full.yml">
  <img alt="build 3.7 full status" title="build 3.7 full status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/typedparser/build-py37-full.yml?branch=main&label=python%203.7%20full" />
</a>
<a href="https://github.com/simon-ging/typedparser/actions/workflows/build-py312-full.yml">
  <img alt="build 3.12 full status" title="build 3.12 full status" src="https://img.shields.io/github/actions/workflow/status/simon-ging/typedparser/build-py312-full.yml?branch=main&label=python%203.12%20full" />
</a>
<img alt="coverage" title="coverage" src="https://raw.githubusercontent.com/simon-ging/typedparser/main/docs/coverage.svg" />
<a href="https://pypi.org/project/typedparser/">
  <img alt="version" title="version" src="https://img.shields.io/pypi/v/typedparser?color=success" />
</a>
</p>

Typing extension for python argparse using [attrs](https://www.attrs.org/en/stable/).

Includes typechecking and conversion utilities to parse a dictionary into an attrs instance. 

## Install

Requires `python>=3.7`

```bash
pip install typedparser
```

## Basic usage

1. Create an attrs class (decorate with `@attr.define`). Note that optional arguments must also be typed as optional.
2. Define and type the fields with `typedparser.add_argument` - the syntax extends [add_argument from argparse](https://docs.python.org/3/library/argparse.html#the-add-argument-method).
3. Parse the args with `TypedParser` and enjoy args with type hints. Disable typechecking by setting `strict=False`.

~~~python
from typing import Optional
from attrs import define
from typedparser import add_argument, TypedParser


@define
class Args:   
    # omit the argument name to have it inferred from the field name
    foo: str = add_argument(positional=True)
    bar: int = add_argument(shortcut="-b", type=int, default=0)
    opt: Optional[str] = add_argument()

    # # in case you prefer the regular argparse syntax:
    # foo: str = add_argument("foo")
    # bar: int = add_argument("-b", "--bar", type=int, default=0)
    # opt: Optional[str] = add_argument("--opt")
    
    

def main():
    parser = TypedParser.create_parser(Args, strict=True)
    args: Args = parser.parse_args()
    print(args)


if __name__ == "__main__":
    main()

~~~


## Features

* Create commandline arguments with type hints and checks while
staying close to the syntax of the standard library's argparse.
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

## Advanced usage

* Use `TypedParser.from_parser(parser, Args)` to add typing to an existing parser. This is useful
to cover usecases like subparsers or argument groups.
* Snippet for argument lists `xarg: List[int] = add_argument(shortcut="-x", type=int, action="append", help="Xarg", default=[])`,
use as `-x 1 -x 2` to get `[1, 2]` in the args instance.

### Usage of attr utilities

Define the class hierarchy and parse the input using `attrs_from_dict`.
Use `@define(slots=False)` to allow multiple inheritance and setting attributes later.

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
* Set `_allow_extra_keys = True` in the class definition to allow unknown fields in the input

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

## Install locally and run tests

Clone repository and cd into. Setup python 3.7 or higher. 
Note: Some tests are skipped for python 3.7.

~~~bash
pip install -e .
pip install pytest pytest-cov pylint
pylint typedparser

# run tests
python -m pytest --cov
pylint tests
~~~
