"""
This test will import all modules in typedparser and check that all imports are sane.

Note: We do not want to depend on packg https://github.com/simon-ging/packg due to circular ref.
Therefore we copy paste module packg.import_from_source here.
"""

import pytest

from typedparser.import_from_source_copy import (
    ImportFromSourceChecker,
    apply_visitor,
    recurse_modules,
)

module_list = list(recurse_modules("typedparser", ignore_tests=True, packages_only=False))


@pytest.mark.parametrize("module", module_list)
def test_imports_from_source(module: str) -> None:
    print(f"Importing: {module}")
    apply_visitor(module=module, visitor=ImportFromSourceChecker(module))
