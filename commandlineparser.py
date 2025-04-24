#!/usr/bin/env python3

"""Decorators and class for parsing command lines"""
import argparse
import sys


# pylint: disable=W0622 (redefined-builtin)
# pylint: disable=R0903 (too-few-public-methods)
# pylint: disable=R0902 (too-many-instance-attributes)
# pylint: disable=R0913 (too-many-arguments)
# pylint: disable=R0917 (too-many-positional-arguments)

# Use regular class instead of dataclass because they can be constructed like a
# regular class instantiation rather than having to wrap the args and keyword
# arguments into an explicit list and hash


class Argument:
    """Encapsulate the details of creating command line arguments. This class
       can be used for both global arguments that apply to the application as
       a whole and sub-command arguments specific to that sub-command"""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Command:
    """Encapsulates the details of each command to be parsed from the command line."""
    def __init__(self, name, commands=None, args=None,
                 mutually_exclusive_args=None, mutually_required=False,
                 func_args=None, **kwargs):
        self.name = name
        self.commands = commands or []
        self.args = args or []
        self.mutually_exclusive_args = mutually_exclusive_args or []
        self.mutually_required = mutually_required
        self.func_args = func_args
        self.parent_name = None
        # Typically the help message and other flags for add_parser()
        self.kwargs = kwargs


class CommandLineParser:
    """Class to enapsulate the details needed to parse the command line. Detailed
       data on the command line to be parsed is supplied to the constructor."""
    def __init__(self, global_arguments, commands):
        self.main_parser = self.create_parser(global_arguments, commands)

    def create_parser(self, global_arguments, commands):
        """Create the top level command parser and attach parsers for sub-commands"""
        main_parser = argparse.ArgumentParser()

        # Set global arguments on the top level parser.
        for arg in global_arguments:
            main_parser.add_argument(*arg.args, **arg.kwargs)

        # Create a sub parser to attach the commands parsers
        main_sub_cmd_parser = main_parser.add_subparsers(title="Commands")

        # commands is a list of Command objects.
        # For each one:
        # - create a sub parser
        # - add each argument to the sub parser
        # - set a default value that contains the command hash and a lambda that
        #   retrieves the arguments from the parsed namespace and supplies then
        #   as arguments to the decorated function which runs the command
        #
        # When the .parse_args() of the parser is run the resulting namespace
        # will contain a 'cmd' entry which can be used to get the function to
        # and also has a 'func_args' with the lambda which creates the
        # arguments to the command function.
        def add_command(cmd, sub_cmd_parser, parent_name):
            cmd.parent_name = parent_name
            parser = sub_cmd_parser.add_parser(cmd.name, **cmd.kwargs)
            for arg in cmd.args:
                parser.add_argument(*arg.args, **arg.kwargs)
            if cmd.mutually_exclusive_args:
                group = parser.add_mutually_exclusive_group(
                        required=cmd.mutually_required)
                for muarg in cmd.mutually_exclusive_args:
                    group.add_argument(*muarg.args, **muarg.kwargs)

            if cmd.commands:
                sub_sub_cmd_parser = parser.add_subparsers(
                        title=f"{cmd.name} commands")
                for c in cmd.commands:
                    add_command(c, sub_sub_cmd_parser, cmd.name)

            if not cmd.func_args:
                cmd.func_args = lambda ns: [getattr(ns, self._arg_name(arg.args[0]))
                                            for arg in ns.cmd.args] + \
                                           [getattr(ns, self._arg_name(arg.args[0]))
                                            for arg in ns.cmd.mutually_exclusive_args]
            parser.set_defaults(cmd=cmd)

        for cmd in commands:
            add_command(cmd, main_sub_cmd_parser, "main")

        # wrap ArgumentParser.parse_args() to make it act like one sub command
        # is required. No required keyword for sub-parsers until py 3.7
        def parse(args):
            ns = main_parser.original_parse_args(args)
            if not hasattr(ns, "cmd"):
                main_parser.print_help()
                sys.exit(1)
            return ns

        main_parser.original_parse_args = main_parser.parse_args
        main_parser.parse_args = parse
        return main_parser

    @staticmethod
    def _arg_name(arg):
        """Convert the argument name to a valid python attribute name"""
        return arg.strip("-").replace("-", "_")

    def parse_args(self, args):
        """Parse command line arguments and run the resulting namespace created
           by argparse"""
        return self.main_parser.parse_args(args)

    @staticmethod
    def true_false(flag):
        """Check true/false argument string"""
        if flag == "true":
            return True
        if flag == "false":
            return False
        return None
