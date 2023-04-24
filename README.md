# typedparser

<p align="center">
<a href="https://github.com/gingsi/typedparser/actions/workflows/build_py37.yml">
  <img alt="build 3.7 status" title="build 3.7 status" src="https://img.shields.io/github/actions/workflow/status/gingsi/typedattr/build_py37.yml?branch=main&label=build%203.7" />
</a>
<a href="https://github.com/gingsi/typedparser/actions/workflows/build_py39.yml">
  <img alt="build 3.9 status" title="build 3.9 status" src="https://img.shields.io/github/actions/workflow/status/gingsi/typedattr/build_py39.yml?branch=main&label=build%203.9" />
</a>
<img alt="coverage" title="coverage" src="https://raw.githubusercontent.com/gingsi/typedparser/main/docs/coverage.svg" />
<a href="https://pypi.org/project/typedparser/">
  <img alt="version" title="version" src="https://img.shields.io/pypi/v/typedparser?color=success" />
</a>
</p>

Typing extension for python argparse using [attrs](https://www.attrs.org/en/stable/) and
[typedattr](https://github.com/gingsi/typedattr).

Why use this library? It allows creating arguments with type hints and checks while 
staying very close to the syntax of the standard library's argparse.

## Install

Requires `python>=3.7`

```bash
pip install typedparser
```

## Usage

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
