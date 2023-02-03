__all__ = [
    "beet_default",
]

from beet import Context, Function, JsonFile
import click


def beet_default(ctx: Context):
    click.secho("Loading documentation configuration files...", fg="yellow")
