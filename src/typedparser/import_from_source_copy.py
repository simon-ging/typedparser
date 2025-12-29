"""
Note: We do not want to depend on packg https://github.com/simon-ging/packg due to circular ref.
Therefore we copy paste module packg.testing.import_from_source here.
"""

import logging
import site
import sys
import sysconfig
import traceback
from ast import ImportFrom, NodeVisitor, parse
from importlib import import_module
from importlib import util as import_util
from importlib.machinery import ModuleSpec
from importlib.metadata import distributions
from os import path
from pkgutil import iter_modules
from typing import Any, Iterator, List, Optional, Set, Tuple, Union


def format_exception(e, with_traceback=False) -> str:
    error_str, error_name = str(e), type(e).__name__
    if error_str == "":
        out_str = error_name
    else:
        out_str = f"{error_name}: {error_str}"

    if not with_traceback:
        return out_str

    tb_list = traceback.format_tb(e.__traceback__)
    tb_str = "".join(tb_list)
    return f"{tb_str}{out_str}"


def get_installed_top_level_packages() -> List[str]:
    """
    Return a sorted list of top-level import names provided by all
    installed distributions in the current environment.
    """
    names: Set[str] = set()

    for dist in distributions():
        # Most wheels/eggs ship a top_level.txt listing the import roots
        top_level = dist.read_text("top_level.txt")
        if not top_level:
            continue

        for line in top_level.splitlines():
            name = line.strip()
            if not name:
                continue
            # optional: skip private/internal names
            if name.startswith("_"):
                continue
            names.add(name)

    return sorted(names)


def is_stdlib(module_name: str, verbose: bool = False) -> Optional[bool]:
    if verbose:
        print(f"---------- Checking if {module_name} is stdlib")

    if hasattr(sys, "stdlib_module_names"):
        # python 3.10 check
        if module_name in sys.stdlib_module_names:
            return True
        return False

    spec = import_util.find_spec(module_name)
    if spec is None or spec.origin is None:
        if verbose:
            print(f"Could not find spec for module {module_name}. {spec=}")
        return None

    origin = spec.origin
    if verbose:
        print(f"Module {module_name} has {origin=}")

    # Built-in modules have origin == 'built-in'
    if origin == "built-in" or origin == "frozen":
        return True

    # Standard library modules live inside sys.base_prefix / sys.exec_prefix
    stdlib_path = sysconfig.get_paths()["stdlib"]
    site_dirs = get_site_dirs()
    if verbose:
        print(f"Standard library path: {stdlib_path}")
        print(f"Site dirs: {site_dirs}")

    # If inside site-packages → not stdlib
    for d in site_dirs:
        if origin.startswith(d):
            return False

    # If inside stdlib directory → stdlib
    return origin.startswith(stdlib_path)


def get_site_dirs() -> Set[str]:
    dirs = set()

    # purelib & platlib (where Python installs packages)
    purelib = sysconfig.get_paths().get("purelib")
    platlib = sysconfig.get_paths().get("platlib")

    if purelib:
        dirs.add(purelib)
    if platlib:
        dirs.add(platlib)

    # site-packages from site.getsitepackages(), if available
    if hasattr(site, "getsitepackages"):
        for d in site.getsitepackages():
            dirs.add(d)

    return dirs


def _is_test_module(module_name: str) -> bool:
    components = module_name.split(".")

    return len(components) >= 2 and components[1] == "tests"


def _is_package(module_spec: ModuleSpec) -> bool:
    return module_spec.origin is not None and module_spec.origin.endswith("__init__.py")


def recurse_modules(
    module_name: str,
    ignore_tests: bool = True,
    packages_only: bool = False,
    ignore_main: bool = False,
) -> Iterator[str]:
    if ignore_tests and _is_test_module(module_name):
        return

    module_spec = import_util.find_spec(module_name)

    if module_spec is not None and module_spec.origin is not None:
        if not (packages_only and not _is_package(module_spec)):
            yield module_name

        for child in iter_modules([path.dirname(module_spec.origin)]):
            if child.ispkg:
                yield from recurse_modules(
                    f"{module_name}.{child.name}",
                    ignore_tests=ignore_tests,
                    packages_only=packages_only,
                )
            if packages_only:
                continue
            if ignore_main and child.name == "__main__":
                continue
            yield f"{module_name}.{child.name}"


class ImportFromSourceChecker(NodeVisitor):
    def __init__(
        self,
        module: str,
        ignore_modules: Optional[Union[List, Tuple]] = None,
        this_package_only: bool = False,
    ):
        """
        Visitor that checks all import statements in the given module and runs the imports.

        Args:
            module: The module to check imports for.
            ignore_modules: A list of modules to ignore import errors for.
            this_package_only: If true, only check imports within the same top-level package.
                This will speed up the imports because it will never import things like numpy,
                however if you have a bad import like "import doesnotexist" it will not be caught.
        """
        ignore_modules = list(ignore_modules) if ignore_modules is not None else []
        module_spec = import_util.find_spec(module)
        is_pkg = (
            module_spec is not None
            and module_spec.origin is not None
            and module_spec.origin.endswith("__init__.py")
        )

        self._module = module if is_pkg else ".".join(module.split(".")[:-1])
        self._top_level_module = self._module.split(".")[0]
        self._ignore_modules = ignore_modules
        self._this_package_only = this_package_only

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        # Skip imports that are indented (inside functions, if statements, etc.)
        if node.col_offset > 0:
            return

        # Check that there are no relative imports that attempt to read from a parent module.
        # We've found that there generally is no good reason to have such imports.
        if node.level >= 2:
            raise ValueError(
                f"Import in {self._module} attempts to import from parent module using "
                f"relative import. Please switch to absolute import instead."
            )

        # Figure out which module to import in the case where this is a...
        if node.level == 0:
            # (1) absolute import where a submodule is specified
            assert node.module is not None
            module_to_import: str = node.module
        elif node.module is None:
            # (2) relative import where no module is specified (ie: "from . import foo")
            module_to_import = self._module
        else:
            # (3) relative import where a submodule is specified (ie: "from .bar import foo")
            module_to_import = f"{self._module}.{node.module}"

        if self._this_package_only:
            # We're only looking at imports of objects defined inside this top-level package
            # However this can mask import problems
            if not module_to_import.startswith(self._top_level_module):
                return
        if is_stdlib(module_to_import):
            # Skip testing stdlib imports because they will break one way or another
            return

        # Actually import the module and iterate through all the objects potentially exported by it.
        print(f"    Importing module: {module_to_import}")
        try:
            module = import_module(module_to_import)
        except Exception as e:
            for ignore_module in self._ignore_modules:
                if module_to_import == ignore_module or module_to_import.startswith(
                    f"{ignore_module}."
                ):
                    print(
                        f"packg.testing.import_from_source: Ignore exception in module "
                        f"{module_to_import}\n{format_exception(e)}"
                    )
                    return
            raise e
        for alias in node.names:
            if not hasattr(module, alias.name):
                if alias.name == "*":
                    continue
                attr = import_module(f"{module_to_import}.{alias.name}")
            else:
                attr = getattr(module, alias.name)

            # For some objects (pretty much everything except for classes and functions),
            # we are not able to figure out which module they were defined in...
            # in that case there's not much we can do here, since we cannot
            # easily figure out where we *should* be importing this from in the first place.
            if isinstance(attr, type) or callable(attr):
                try:
                    attribute_module = attr.__module__
                except AttributeError:
                    # e.g. functools.partial outupt does not have __module__ and breaks here
                    continue
            else:
                continue

            # Figure out where we should be importing this class from, and assert that
            # the *actual* import we found matches the place we *should* import from.
            should_import_from = self._get_module_should_import(module_to_import=attribute_module)
            if module_to_import != should_import_from:
                logging.warning(
                    f"(Potential false positive) "
                    f"Imported {alias.name} from {module_to_import}, "
                    f"which is not the public module where this object "
                    f"is defined. Please import from {should_import_from} instead."
                )

    def _get_module_should_import(self, module_to_import: str) -> str:
        """
        This function figures out the correct import path for "module_to_import" from the
        "self._module" module in this instance. The trivial solution here would be to always
        just return "module_to_import", but we want to actually take into account the fact that
        some submodules can be "private" (ie: start with an "_"), in which case we should only
        import from them if self._module is internal to that private module.
        """
        module_components = module_to_import.split(".")
        result: List[str] = []

        for component in module_components:
            if component.startswith("_") and not self._module.startswith(".".join(result)):
                break
            result.append(component)

        return ".".join(result)


def apply_visitor(module: str, visitor: NodeVisitor) -> None:
    module_spec = import_util.find_spec(module)
    assert module_spec is not None
    assert module_spec.origin is not None

    source_file = module_spec.origin
    if source_file.endswith(".abi3.so"):
        print(f"Skipping rust binary: {source_file}")
        return

    with open(module_spec.origin, "r", encoding="utf-8") as fh:
        ast = parse(source=fh.read(), filename=module_spec.origin)
    visitor.visit(ast)
