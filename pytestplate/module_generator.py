from __future__ import annotations
import ast
import pathlib


class PyTestModuleGenerator(ast.NodeVisitor):

    """Class for automatically generating a test module from a single python module"""

    linesep = "\n"
    tab = "    "
    blankline = ""
    default_assert_code = 'assert False, "not implemented"'
    default_docstring = '"""Should ..."""'
    tests_dir_name = "tests"

    def __init__(self, module: pathlib.Path, *args, **kwargs) -> None:
        """Initialize `PyTestModuleGenerator`.

        Args:
            module (pathlib.Path): Path to the python module to read
        """
        self.module = module
        self.tests_dir = module.parent / self.tests_dir_name
        super().__init__(*args, **kwargs)
        self.module_docstring = ""
        self.imports = set()
        self.lines = []
        self.indent = 0
        self.current_cls = None

    @property
    def code(self) -> str:
        """Generated code.

        Returns:
            str
        """
        lines = (
            [self.module_docstring] + list(self.imports) + 2 * [self.blankline] + self.lines
        )
        return self.linesep.join(lines).strip() + self.linesep

    def visit_Module(self, node: ast.Module) -> None:
        """Visit the Module and update module level generated code.

        Args:
            node (ast.Module)
        """
        self.module_docstring = f'"""Unit tests for `{self.module.name}`"""'
        self.imports.add("import pytest")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function and update function level generated code.

        Args:
            node (ast.FunctionDef)
        """
        arg_self = "self" if self.current_cls is not None else ""
        blanklines = 2 if self.current_cls is None else 1
        self.lines.extend(
            [
                self.tab * self.indent + f"def test_{node.name}({arg_self}):",
                self.tab * (self.indent + 1) + self.default_docstring,
                self.tab * (self.indent + 1) + self.default_assert_code,
            ]
        )
        for _ in range(blanklines):
            self.lines.append(self.blankline)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class and update class level generated code.

        Args:
            node (ast.ClassDef)
        """
        clsdef_line = self.tab * self.indent + f"class Test{node.name}:"
        self.lines.extend(
            [
                clsdef_line,
                self.tab * (self.indent + 1) + f'"""Tests for class `{node.name}`"""\n',
            ]
        )
        self.indent += 1
        self.current_cls = node.name
        self.generic_visit(node)
        self.current_cls = None
        if self.lines[-2] == clsdef_line:
            self.lines.extend([self.tab * self.indent + "pass", self.blankline])
        self.indent -= 1
        self.lines.append(self.blankline)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an async function and update async function level generated code.

        Args:
            node (ast.AsyncFunctionDef)
        """
        blanklines = 2 if self.current_cls is None else 1
        self.lines.extend(
            [
                self.tab * self.indent + "@pytest.mark.asyncio",
                self.tab * self.indent + f"async def test_{node.name}():",
                self.tab * (self.indent + 1) + self.default_docstring,
                self.tab * (self.indent + 1) + self.default_assert_code,
            ]
        )
        for _ in range(blanklines):
            self.lines.append(self.blankline)
        self.generic_visit(node)

    def generate(self) -> PyTestModuleGenerator:
        """Generate the test code from the python module by visiting all nodes.

        Returns:
            PyTestModuleGenerator
        """
        module_txt = ast.parse(self.module.read_text())
        self.visit(module_txt)
        return self

    def write(self) -> None:
        """Write the generated test code out to the `tests` directory. Creates the directory and
        a `conftest.py` file if they do not already exist.
        """
        self.tests_dir.mkdir(exist_ok=True)
        (self.tests_dir / "conftest.py").touch(exist_ok=True)
        (self.tests_dir / f"test_{self.module.stem}.py").write_text(self.code)
