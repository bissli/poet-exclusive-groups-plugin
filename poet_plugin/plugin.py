from cleo.events.console_command_event import ConsoleCommandEvent
from cleo.events.console_events import COMMAND
from cleo.events.event_dispatcher import EventDispatcher
from cleo.io.inputs.input import Input
from poetry.console.application import Application
from poetry.console.commands.installer_command import InstallerCommand
from poetry.core.packages.project_package import ProjectPackage
from poetry.plugins.application_plugin import ApplicationPlugin


def option_groups(io_input: Input, name: str) -> set[str]:
    """Group names passed to a repeatable group option.

    Parameters
    ----------
    io_input : Input
        Command input, already bound to the command's definition.
    name : str
        'only' or 'without'.

    Returns
    -------
    set[str]
        Each value split on commas and stripped, as Poetry splits them, so
        '--only dev,test' names two groups. Empty when the command has no
        such option.
    """
    if not io_input.has_option(name):
        return set()
    return {
        group.strip()
        for groups in io_input.option(name)
        for group in groups.split(',')
        }


class PEGPlugin(ApplicationPlugin):
    def activate(self, application: Application) -> None:
        """Register the group filter on every console command.
        """
        application.event_dispatcher.add_listener(COMMAND, self.remove_dependencies)

    def remove_dependencies(
        self,
        event: ConsoleCommandEvent,
        event_name: str,
        dispatcher: EventDispatcher) -> None:
        """Drop the groups --only and --without exclude before Poetry resolves.

        Parameters
        ----------
        event : ConsoleCommandEvent
            The command about to run. Any command other than an installer
            command passes through untouched.
        event_name : str
            Unused. The listener signature requires it.
        dispatcher : EventDispatcher
            Unused. The listener signature requires it.
        """
        if not isinstance(event.command, InstallerCommand):
            return
        command: InstallerCommand = event.command
        installer = command.installer

        package: ProjectPackage = installer._package  # noqa
        only_flag = option_groups(event.io.input, 'only')
        without_flag = option_groups(event.io.input, 'without')

        if only_flag:
            package = package.with_dependency_groups(only_flag, only=True)
        if without_flag:
            package = package.without_dependency_groups(without_flag)

        command.installer._package = package
