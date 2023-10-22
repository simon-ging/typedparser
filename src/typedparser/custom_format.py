import argparse


class CustomArgparseFmt(argparse.RawDescriptionHelpFormatter):
    """
    Custom formatter for argparse.

    Usage:
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=CustomArgparseFmt)

    Format changes:
        No removal of newlines from descriptions
        Show default values for arguments
        Show argument types
        Wider default max_help_position
    """

    def __init__(self, prog, indent_increment=4, max_help_position=None, width=None):
        # default setting for width
        if width is None:
            import shutil

            width = shutil.get_terminal_size().columns
            width -= 2
        if max_help_position is None:
            max_help_position = min(width // 2, 36)
        super().__init__(
            prog,
            indent_increment=indent_increment,
            max_help_position=max_help_position,
            width=width,
        )

    def _format_action(self, action):
        # source: argparse.MetavarTypeHelpFormatter
        # without this change, defaults are only shown if help is defined for the arg
        if action.default is not None and action.help is None:
            action.help = argparse.SUPPRESS
        return super()._format_action(action)

    def _get_help_string(self, action):
        # Support argparse.SUPPRESS as input for help
        if action.help == argparse.SUPPRESS:
            help_str_add = "default: %(default)s"
            help_str = ""
        else:
            help_str_add = " (default: %(default)s)"
            help_str = action.help
        if action.choices is not None:
            help_str_add = f"{help_str_add} choices: %(choices)s"
        if "%(default)" not in action.help:
            if action.default is not argparse.SUPPRESS:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help_str += help_str_add
        return help_str

    def _get_default_metavar_for_optional(self, action):
        try:
            return action.type.__name__
        except AttributeError:
            return "none"

    def _get_default_metavar_for_positional(self, action):
        try:
            return action.type.__name__
        except AttributeError:
            return "none"
