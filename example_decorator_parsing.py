#!/usr/bin/env python3

'''BlueSky command line interface'''

import os
import sys
import configparser
import logging

from commandlineparser import Command, Argument, CommandLineParser
import bluesky
import shared


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
    COMMANDS = [Command('did',
                        [Argument('handle', nargs='?', help="user's handle")],
                        help="show a user's did"),
                Command('profile',
                        [Argument('handle', nargs='?',
                                  help="user's handle"),
                         Argument('--full', '-f', action='store_true',
                                  help="show user's profile")],
                        help='Show more details of each user')]

    def __init__(self, args):
        """Command Line Main Entry Point"""
        # Parse the command line
        self.ns = CommandLineParser(self.GLOBAL_ARGUMENTS,
                                    self.COMMANDS).parse_args(args)

        # Setting some logging details based on the command line args
        shared.DEBUG = self.ns.log_level == logging.DEBUG
        logging.basicConfig(level=self.ns.log_level)
        self.logger = logging.getLogger(__name__)

        # Read config based on command line args or defaults
        config = (self.ns.config or
                  os.environ.get('DBCONFIG') or
                  BlueSkyCommandLine.CONFIG_PATH_DEFAULT)
        self.handle, self._password = self._get_config(config)

        # Create the bluesky client that interacts with the BlueSky API
        self.bs = bluesky.BlueSky(self.handle, self._password)

    def run(self):
        """Run the function for the command line given to the constructor"""
        # self.ns is populated when we call CommandLineParser.parse_args() in the
        # constructor. self.ns contains the name of the function to run which we can
        # lookup on this obejct. It also contains 'func_args' lambda that
        # assembles the function arguments from the parsed command line.
        getattr(self, self.ns.cmd.name)(*self.ns.func_args(self.ns))

    @staticmethod
    def _get_config(path):
        """Read config data and return"""
        cp = configparser.ConfigParser()
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        cp.read(path)
        return cp.get('auth', 'user'), cp.get('auth', 'password')

    def did(self, handle):
        """Print the DID of the given user"""
        hand = handle or self.handle
        if '.' not in hand:
            hand += '.bsky.social'
        did = self.bs.profile_did(hand)
        if did:
            print(did)
        else:
            print(f"No DID found for {hand}")

    def profile(self, handle, full):
        """Print the profile entry of the given user handle"""
        profile = self.bs.get_profile(handle)
        if profile:
            print(f"Profile: {profile.display_name or ''}@{profile.handle}")
            if full:
                print(f"Profile Link: https://bsky.app/profile/{profile.handle}")
                print(f"DID: {profile.did}")
                print(f"Created at: {profile.created_at}")
        else:
            print(f"{handle} profile not found")


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
