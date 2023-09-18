"""Print loaded configurations."""
import rich

from .. import configs
from ._base import command


@command.command("configs")
def subcommand():
    """Print loaded configurations."""
    main()


def main():
    """Print loaded configurations."""
    rich.print(configs.configs)
