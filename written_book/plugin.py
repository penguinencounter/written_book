__all__ = [
    "beet_default",
]

import click
from beet import Context


def beet_default(ctx: Context):
    click.secho("Loading documentation configuration files...", fg="yellow")
