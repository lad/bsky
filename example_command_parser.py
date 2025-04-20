#!/usr/bin/env python3

'''BlueSky command line interface'''

# pylint can't see that we use User and Msg classes but find them dynamically using
# globals()
# pylint: disable=W0611 (unused-import)

import os
import sys
import configparser
import logging

from commandlineparser import Command, Argument, CommandLineParser
import bluesky
import shared

from blueskyuser import User
from blueskymsg import Msg


class BlueSkyCommandLine:
    """A command line client for the BlueSky API"""
    CONFIG_PATH_DEFAULT = os.path.join(os.getcwd(), '.config')
    GLOBAL_ARGUMENTS = [Argument("--critical", action="store_const",
                                 dest="log_level", const=logging.CRITICAL,
                                 help='Set log level to CRITICAL'),
                        Argument('--error', '-e', action='store_const',
                                 dest="log_level", const=logging.ERROR,
                                 help='Set log level to ERROR'),
                        Argument('--warning', '-w', action='store_const',
                                 dest="log_level", const=logging.WARNING,
                                 default=logging.WARNING,
                                 help='Set log level to WARNING [default]'),
                        Argument('--info', '-i', action='store_const',
                                 dest="log_level", const=logging.INFO,
                                 help='Set log level to INFO'),
                        Argument('--debug', '-d', action='store_const',
                                 dest="log_level", const=logging.DEBUG,
                                 help='Set log level to DEBUG'),
                        Argument('--verbose', '-v', action='store_const',
                                 dest="log_level", const=logging.DEBUG,
                                 help='Synonym for --debug'),
                        Argument('--config', '-c', dest='config', action='store',
                                 help='config file or $BSCONFIG or $PWD/.config')]
    USER_COMMANDS = [Command('did', None,
                             [Argument('handle', nargs='?', help="user's handle")],
                             help="show a user's did"),
                     Command('profile', None,
                             [Argument('handle', nargs='?', help="user's handle")],
                             help='Show more details of each user')]
    MSG_COMMANDS = [Command('unread', help='show number of unread messages'),
                    Command('gets', None,
                            [Argument('--since', '-s', action='store',
                                      help='Date limit (e.g. today/yesterday/3 days '
                                           'ago'),
                             Argument('--all', '-a', action='store_true',
                                      help='Show both read and unread notifications'),
                             Argument('--count', '-c', action='store', type=int,
                                      help='Max number of notifications to show'),
                             Argument('--mark', '-m', action='store_true',
                                      help='Mark notifications as seen')],
                            help='Show notifications')]
    COMMANDS = [Command('user', USER_COMMANDS),
                Command('msg', MSG_COMMANDS)]

    def __init__(self, args):
        """Command Line Main Entry Point"""
        # Parse the command line
        self.main_parser = CommandLineParser(self.GLOBAL_ARGUMENTS, self.COMMANDS)
        self.ns = self.main_parser.parse_args(args)

        # Setting some logging details based on the command line args
        shared.DEBUG = self.ns.log_level == logging.DEBUG
        logging.basicConfig(level=self.ns.log_level)
        self.logger = logging.getLogger(__name__)

        # Read config based on command line args or defaults
        config = (self.ns.config or
                  os.environ.get('DBCONFIG') or
                  BlueSkyCommandLine.CONFIG_PATH_DEFAULT)
        self.handle, self._password = self.get_config(config)

        # Create the bluesky client that interacts with the BlueSky API
        self.bs = bluesky.BlueSky(self.handle, self._password)

    def run(self):
        """Run the function for the command line given to the constructor"""

        # self.ns is populated when we call CommandLineParser.parse_args() in the
        # constructor. self.ns contains the name of the parent command and the name
        # of the command chosen. The parent command is the name of the class to
        # instantiate and the command name is the name of the method to run on
        # that object. It also contains 'func_args' lambda that assembles the
        # function arguments from the parsed command line.

        try:
            cls = globals()[self.ns.cmd.parent_name.capitalize()]
        except KeyError:
            self.main_parser.parse_args([self.ns.cmd.name, '-h'])
            sys.exit(1)

        cls(self.bs, self.ns).run()

    @staticmethod
    def get_config(path):
        """Read config data and return"""
        cp = configparser.ConfigParser()
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        cp.read(path)
        return cp.get('auth', 'user'), cp.get('auth', 'password')


def main():
    """main entrypoint to create and run the command line client"""
    try:
        BlueSkyCommandLine(sys.argv[1:]).run()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
    except Exception as ex:     # pylint: disable=broad-except
        if shared.DEBUG:
            import traceback    # pylint: disable=import-outside-toplevel
            traceback.print_exc()
        else:
            print(type(ex))
            print(ex)
        sys.exit(1)


if __name__ == '__main__':
    main()
