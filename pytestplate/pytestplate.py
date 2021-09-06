import pathlib
from typing import Tuple

import click

from pytestplate.module_generator import PyTestModuleGenerator


def loop_modules(modules: Tuple[pathlib.Path, ...]):
    """Loop through each module provided by the CLI.

    Args:
        modules (Tuple[pathlib.Path, ...])
    """
    for module in modules:
        if module.is_dir() or module.name.startswith("_"):
            continue
        click.echo(f"\u2794 Generating test boilerplate for {module.name}")
        gen = PyTestModuleGenerator(module).generate()
        gen.write()


@click.command()
@click.argument(
    "modules", nargs=-1, required=True, type=lambda s: pathlib.Path(s).absolute()
)
def cli(modules):
    """MODULES is a list all Python modules to generate tests for."""
    click.secho("Running pytestplate...", bold=True)
    loop_modules(modules)
    click.secho("Done", bold=True)


if __name__ == "__main__":
    cli()
