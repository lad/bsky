#!/usr/bin/env python3

'''Decorators and class for parsing command lines'''
import argparse
import sys

# pylint: disable=W0622 (redefined-builtin)


def command(name, help=''):
    """A decorator to create commands that can be parsed from the command line"""
    # Create an entry in this to keep track of each command declared
    CommandLineParser.COMMANDS[name] = {'name': name,
                                        'args': [],
                                        'help': help}

    def decorator(func):
        # Save a reference to the decorated function
        CommandLineParser.COMMANDS[name]['func'] = func
        return func
    return decorator


def arg_to_name(arg):
    """Convert the argument name to a valid python attribute name"""
    return arg.strip('-').replace('-', '_')


def argument(cmd_name, *aargs, **kwargs):
    """A decorator used to declare each argument for the given command name"""
    def decorator(func):
        lst = CommandLineParser.COMMANDS[cmd_name]['args']
        CommandLineParser.COMMANDS[cmd_name]['args'] = [{'name': arg_to_name(aargs[0]),
                                                         'args': aargs,
                                                         'kwargs': kwargs}] + lst
        return func
    return decorator


def global_argument(*args, **kwargs):
    '''A decorator used to declare global arguments for the command line'''
    CommandLineParser.GLOBAL_ARGUMENTS.append((args, kwargs))

    def decorator(func_or_cls):
        return func_or_cls
    return decorator


class CommandLineParser:
    """Class to enapsulate the details needed to parse the command line using
       details declared by the `@command` and `@argument` function decorators"""
    GLOBAL_ARGUMENTS = []
    COMMANDS = {}

    def __init__(self, args):
        self.args = args
        self.main_parser = self.create_parser()

    def parse_args(self):
        """Parse command line arguments and return namespace results"""
        return self.main_parser.parse_args(self.args)

    def create_parser(self):
        """Create the top level command parser and attach parsers for sub-commands"""
        main_parser = argparse.ArgumentParser()

        # Set global arguments. The contents of GLOBAL_ARGUMENTS is populared
        # by the @global_argument decorator.
        for args, kwargs in self.GLOBAL_ARGUMENTS:
            main_parser.add_argument(*args, **kwargs)

        # Create a sub parser to attach the commands parsers
        sub_cmd_parser = main_parser.add_subparsers(title='Commands')

        # These contents of COMMANDS is populated by the @command and @argument
        # decorators. Each entry is hash with the details of the command (see the
        # decorators for details). For each one:
        # - create a sub parser
        # - add each argument to the sub parser
        # - set a default value that contains the command hash and a lambda that
        #   retrieves the arguments from the parsed namespace and supplies then
        #   as arguments to the decorated function which runs the command
        #
        # When the .parse_args() of the parser is run the resulting namespace
        # will contain a 'cmd' entry which can be used to get the function to
        # run (in 'func') and also has a 'func_args' with the lambda which
        # creates the arguments to the command function.
        for cmd in self.COMMANDS.values():
            parser = sub_cmd_parser.add_parser(cmd['name'], help=cmd['help'])
            for arg in cmd['args']:
                parser.add_argument(*arg['args'], **arg['kwargs'])

            # Set a default which will get populated into the namespace result
            # from .parse_args(). Also contains the lambda that assembles the
            # command function arguments from the namespace returned by
            # ArgumentParser.parse_args(), i.e. the parsed values from the
            # command line
            parser.set_defaults(cmd=cmd,
                                func_args=lambda ns: [getattr(ns, arg['name'])
                                                      for arg in ns.cmd['args']])

        # wrap ArgumentParser.parse_args() to make it act like one sub command
        # is required. No required keyword for sub-parsers until py 3.7
        def parse(args):
            ns = main_parser.original_parse_args(args)
            if not hasattr(ns, 'cmd'):
                main_parser.print_help()
                sys.exit(1)
            return ns

        main_parser.original_parse_args = main_parser.parse_args
        main_parser.parse_args = parse
        return main_parser
