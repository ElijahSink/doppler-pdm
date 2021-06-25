from pdm import Core

from .run import Command


def main(core: Core) -> None:
    core.register_command(Command, "run")
