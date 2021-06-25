# STL
import json
import argparse
import subprocess
from typing import Dict, Union, Mapping, Optional, Sequence
from json.decoder import JSONDecodeError

# PDM
from pdm import termui
from pdm.project import Project
from pdm.cli.utils import check_project_file
from pdm.exceptions import PdmUsageError
from pdm.cli.commands.run import Command as RunCommand


def get_doppler_envvars(project: Project) -> Dict[str, str]:
    result = {}
    project.core.ui.echo(
        "Running: `doppler secrets --json --silent`", verbosity=termui.DEBUG
    )
    try:
        p = subprocess.run(
            ["doppler", "secrets", "--json", "--silent"], capture_output=True
        )
    except FileNotFoundError:
        project.core.ui.echo(f"It appears that you do not have doppler installed", True)
        project.core.ui.echo(f"See: https://www.doppler.com/", True)
        return result

    if p.returncode != 0:
        project.core.ui.echo(f"Doppler returned non-zero code: {p.returncode}", True)
    if p.stdout:
        try:
            result = json.loads(p.stdout)
            for varname, value in result.items():
                result[varname] = value["computed"]
        except JSONDecodeError as e:
            project.core.ui.echo("Failed to decode envvars as JSON from Doppler", True)
            project.core.ui.echo(e.msg, True, termui.DETAIL)
    if p.stderr:
        error_msg = "Unknown error from Doppler; check the output of `doppler secrets`"
        error_json = None
        try:
            error_json = json.loads(p.stderr)
            error_msg = error_json["error"]
        except JSONDecodeError as e:
            project.core.ui.echo("Failed to decode envvars as JSON from Doppler", True)
            project.core.ui.echo(e.msg, True, termui.DETAIL)
            project.core.ui.echo("stderr: ", True, termui.DEBUG)
            project.core.ui.echo(p.stderr.decode(), True, termui.DEBUG)
        except (TypeError, KeyError):
            project.core.ui.echo("Unknown error from Doppler", True)
            project.core.ui.echo(json.dumps(error_json, indent=2), True, termui.DETAIL)

        if error_msg == "You must specify a project":
            project.core.ui.echo(
                "Doppler has not been configured in this environment yet", True
            )
            project.core.ui.echo("Try `doppler setup`", True)

    return result


class Command(RunCommand):
    """Run commands or scripts with local packages and Doppler envvars loaded"""

    OPTIONS = ["env", "env_file", "doppler", "help"]

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "-d",
            "--doppler",
            action=argparse.BooleanOptionalAction,
            help="Whether to run this command with envvars loaded from Doppler",
        )
        super().add_arguments(parser)

    def coalesce_env_options(
        self,
        project: Project,
        options: argparse.Namespace,
        global_env_options: Dict,
    ) -> None:
        command_name = options.command

        should_load_from_doppler = bool(global_env_options.get("doppler", None))

        if command_name in (project.scripts or {}):
            script = project.scripts[command_name]
            *_, script_options = self._normalize_script(script)
            if "doppler" in script_options:
                should_load_from_doppler = bool(script_options.get("doppler", None))

        if options.doppler is not None:
            should_load_from_doppler = bool(options.doppler)

        if should_load_from_doppler:
            global_env_options["env"] = {
                **global_env_options.get("env", {}),
                **get_doppler_envvars(project),
            }

    @staticmethod
    def _run_command(
        project: Project,
        args: Union[Sequence[str], str],
        chdir: bool = False,
        shell: bool = False,
        env: Optional[Mapping[str, str]] = None,
        env_file: Optional[str] = None,
        doppler: Optional[bool] = None,
    ) -> None:
        RunCommand._run_command(project, args, chdir, shell, env, env_file)

    def _show_list(self, project: Project) -> None:
        if not project.scripts:
            return
        columns = ["Name", "Type", "Script", "Description", "Inject Doppler Envvars?"]
        result = []
        for name, script in project.scripts.items():
            if name == "_":
                continue
            kind, value, options = self._normalize_script(script)
            result.append(
                (
                    termui.green(name),
                    kind,
                    str(value),
                    options.get("help", ""),
                    termui.blue("Yes" if options.get("doppler") else "No"),
                )
            )
        project.core.ui.display_columns(result, columns)

    def handle(self, project: Project, options: argparse.Namespace) -> None:
        check_project_file(project)
        if options.list:
            return self._show_list(project)
        global_env_options = project.scripts.get("_", {}) if project.scripts else {}
        assert isinstance(global_env_options, dict)
        if not options.command:
            raise PdmUsageError("No command given")
        self.coalesce_env_options(project, options, global_env_options)
        if project.scripts and options.command in project.scripts:
            self._run_script(project, options.command, options.args, global_env_options)
        else:
            self._run_command(
                project,
                [options.command] + options.args,
                **global_env_options,  # type: ignore
            )
