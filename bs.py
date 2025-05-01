#!/usr/bin/env python3

"""BlueSky command line interface"""

# pylint can't see that we use several claseses that are found dynamically using
# globals(). See the run() method of BlueSkyCommandLine
# pylint: disable=W0611 (unused-import)

import os
import sys
import configparser
import logging
from dataclasses import dataclass

import bluesky
from commandlineparser import Command, Argument, CommandLineParser
from usercmd import UserCmd
from postcmd import PostCmd
from likecmd import LikeCmd
from msgcmd import MsgCmd
import shared


@dataclass
class SearchCommandRequest:
    """Encapsulate fields to represent a search query command"""
    term: str
    author: str
    date_limit: str
    sort_order: str
    is_follow: bool
    is_follower: bool


class BlueSkyCommandLine:
    """A command line client for the BlueSky API"""
    CONFIG_PATH_DEFAULT = os.path.join(os.getcwd(), ".config")
    # Global aruments for the application as a whole
    ARGUMENTS = [Argument("--critical", action="store_const",
                          dest="log_level", const=logging.CRITICAL,
                          help="Set log level to CRITICAL"),
                 Argument("--error", "-e", action="store_const",
                          dest="log_level", const=logging.ERROR,
                          help="Set log level to ERROR"),
                 Argument("--warning", "-w", action="store_const",
                          dest="log_level", const=logging.WARNING,
                          default=logging.WARNING,
                          help="Set log level to WARNING [default]"),
                 Argument("--info", "-i", action="store_const",
                          dest="log_level", const=logging.INFO,
                          help="Set log level to INFO"),
                 Argument("--debug", "-d", action="store_const",
                          dest="log_level", const=logging.DEBUG,
                          help="Set log level to DEBUG"),
                 Argument("--verbose", "-v", action="store_const",
                          dest="log_level", const=logging.DEBUG,
                          help="Synonym for --debug"),
                 Argument("--config", "-c", dest="config", action="store",
                          help="Config file or $BSCONFIG or $PWD/.config")]
    # User sub-commands
    USER = [Command("did", None,
                    [Argument("handle", nargs="?", help="User's handle")],
                    help="Show a user's did"),
            Command("profile", None,
                    [Argument("handle", nargs="?", help="User's handle")],
                    help="Show more details of each user"),
            Command("follows", None,
                    [Argument("handle", nargs="?", help="User's handle"),
                     Argument("--full", "-f", action="store_true",
                              help="Show more details of each user")],
                    help="Show who a user follows"),
            Command("followers", None,
                    [Argument("handle", nargs="?", help="User's handle"),
                     Argument("--full", "-f", action="store_true",
                              help="Show more details of each user")],
                    help="Show the given user's followers"),
            Command("mutuals", None,
                    [Argument("handle", nargs="?", help="User's handle"),
                     Argument("--flag", choices=["both",
                                                 "follows-not-followers",
                                                 "followers-not-follows"],
                              default="both",
                              help="Both show mutuals, follows-not-followers shows "
                                   "users that the given user follows that don't "
                                   "follow back, followers-not-follows shows users "
                                   "that follow the given user that the user doesn't "
                                   "follow back"),
                     Argument("--full", "-f", action="store_true",
                              help="Show more details of each user")],
                    help="Show who follows the given user"),
            Command("reposters", None,
                    [Argument("handle", nargs="?", help="User's handle"),
                     Argument("--since", "-s", action="store",
                              help="Date limit (e.g. today/yesterday/3 days ago"),
                     Argument("--full", "-f", action="store_true",
                              help="Show more details of each user")],
                    help="Show repost users"),
            Command("likes", None,
                    [Argument("--since", "-s", action="store",
                              help="Date limit (e.g. today/yesterday/3 days ago"),
                     Argument("--count", "-c", action="store", type=int,
                              help="Max number of posts to check likes for"),
                     Argument("--date", "-d", action="store_true",
                              help="Show date of each like (more costly)"),
                     Argument("--short",  action="store_true",
                              help="Show a short format output")],
                    help="Show likes for authenticated user")]

    # Post sub-commands
    POST = [Command("get", None,
                    mutually_exclusive_args=[Argument("--uri", action="store",
                                                      help="URI of the post to "
                                                           "display"),
                                             Argument("--url", action="store",
                                                      help="URL of the post to "
                                                           "display")],
                    mutually_required=True,
                    help="Display details of the given post"),
            Command("gets", None,
                    [Argument("handle", nargs="?", help="User's handle"),
                     Argument("--since", "-s", action="store",
                              help="Date limit (e.g. today/yesterday/3 days ago)"),
                     Argument("--count", "-c", type=int, action="store",
                              help="Count of posts to display"),
                     Argument("--original", "-o", action="store_const",
                              dest="post_type",
                              const=bluesky.ORIGINAL_POST,
                              default=bluesky.ORIGINAL_POST,
                              help="Show original posts only"),
                     Argument("--repost", action="store_const",
                              dest="post_type",
                              const=bluesky.REPOST_POST,
                              help="Show reposts only"),
                     Argument("--reply", action="store_const",
                              dest="post_type",
                              const=bluesky.REPLY_POST,
                              help="Show replies only"),
                     Argument("--all", "-a", action="store_const",
                              dest="post_type",
                              const=bluesky.ALL_POST,
                              help="Show all posts types")],
                    func_args=lambda ns: (ns.handle, ns.since, ns.count, ns.post_type),
                    help="Show BlueSky posts"),
            Command("put", None,
                    [Argument("text", action="store", help="Text to post"),
                     Argument("--uri", "-u", action="store_true",
                              help="Show URI of post")],
                    help="Post text to BlueSky"),
            Command("putr", None,
                    [Argument("text", action="store", help="Text to post"),
                     Argument("--mentions", "-m", nargs="+",
                              help="A list of user mentions (no @ required)"),
                     Argument("--uri", "-u", action="store_true",
                              help="Show URI of post")],
                    help="Post rich text to BlueSky"),
            Command("puti", None,
                    [Argument("text", action="store", help="Text to post"),
                     Argument("filename", action="store", help="Path to image file"),
                     Argument("--alt", "-a", action="store", help="Image alt text"),
                     Argument("--uri", "-u", action="store_true",
                              help="Show URI of post")],
                    help="Post image to BlueSky"),
            Command("delete", None,
                    [Argument("uri", action="store", help="URI to delete")],
                    aliases=["del"], help="Delete BlueSky post"),
            Command("search", None,
                    [Argument("term", action="store", help="Term to search for"),
                     Argument("--author", action="store",
                              help="Restrict result to the given author handle"),
                     Argument("--since", "-s", action="store",
                              help="Date limit (e.g. today/yesterday/3 days ago"),
                     Argument("--sort", choices=["top", "latest"], default="top",
                              help="Sort result by top or latest"),
                     Argument("--follow", choices=["true", "false", None],
                              help="Show only posts by users that the authenticated "
                                   "user follows (true) or doesn't follow (false)"),
                     Argument("--follower", choices=["true", "false", None],
                              help="Show only posts by users that are followers "
                                   "(true) or not followers (false) of the "
                                   "authenticated user")],
                    func_args=lambda ns: [SearchCommandRequest(
                         ns.term, ns.author, ns.since, ns.sort,
                         CommandLineParser.true_false(ns.follow),
                         CommandLineParser.true_false(ns.follower))],
                    help="Show posts for a given search string (Lucene search "
                         "strings supported)"),
            Command("likes", None,
                    [Argument("uri", action="store", help="URI to delete"),
                     Argument("--full", "-f", action="store_true",
                              help="Show more details of each user")],
                    help="Show like details of the post")]

    # Like sub-commands
    LIKE = [Command("get", None,
                    args=[Argument("uri", action="store", help="Post URI"),
                          Argument("--count", "-c", action="store_true",
                                   help="Show number of likes")],
                    mutually_exclusive_args=[Argument("--no-details", "-n",
                                                      action="store_true",
                                                      help="Don't show any details "
                                                           "of users"),
                                             Argument("--full", "-f",
                                                      action="store_true",
                                                      help="Show full details of "
                                                           "each user who likes the "
                                                           "post")],
                    help="Show like details of a particular post"),
            Command("gets", None,
                    [Argument("handle", nargs="?", help="User's handle"),
                     Argument("--since", "-s", action="store",
                              help="Date limit (e.g. today/yesterday/3 days ago"),
                     Argument("--count", "-c", type=int, action="store",
                              help="Count of posts to display"),
                     Argument("--original", "-o", action="store_const",
                              dest="post_type",
                              const=bluesky.ORIGINAL_POST,
                              default=bluesky.ORIGINAL_POST,
                              help="Show original posts only"),
                     Argument("--repost", action="store_const",
                              dest="post_type",
                              const=bluesky.REPOST_POST,
                              help="Show reposts only"),
                     Argument("--reply", action="store_const",
                              dest="post_type",
                              const=bluesky.REPLY_POST,
                              help="Show replies only"),
                     Argument("--all", "-a", action="store_const",
                              dest="post_type",
                              const=bluesky.ALL_POST,
                              help="Show all posts types"),
                     Argument("--full", "-f", action="store_true",
                              help="Show full details of each user who likes the "
                                   "post")],
                    func_args=lambda ns: (ns.handle, ns.since, ns.count,
                                          ns.post_type, ns.full),
                    help="Show like details of the found posts"),
            Command("most", None,
                    [Argument("--since", "-s", action="store",
                              help="Date limit (e.g. today/yesterday/3 days ago)"),
                     Argument("--count", "-c", type=int, action="store",
                              help="Count of posts to display"),
                     Argument("handle", nargs="?", help="User's handle"),
                     Argument("--full", "-f", action="store_true",
                              help="Show full details of each user who likes the "
                                   "post"),
                     Argument("--original", "-o", action="store_const",
                              dest="post_type",
                              const=bluesky.ORIGINAL_POST,
                              default=bluesky.ORIGINAL_POST,
                              help="Show original posts only"),
                     Argument("--repost", action="store_const",
                              dest="post_type",
                              const=bluesky.REPOST_POST,
                              help="Show reposts only"),
                     Argument("--reply", action="store_const",
                              dest="post_type",
                              const=bluesky.REPLY_POST,
                              help="Show replies only"),
                     Argument("--all", "-a", action="store_const",
                              dest="post_type",
                              const=bluesky.ALL_POST,
                              help="Show all posts types")],
                    func_args=lambda ns: (ns.handle, ns.since, ns.count,
                                          ns.post_type, ns.full),
                    help="Find users with the most likes for the given posts")]

    # Msg (notification) sub-commands
    MSG = [Command("unread", help="Show number of unread messages"),
           Command("gets", None,
                   [Argument("--since", "-s", action="store",
                             help="Date limit (e.g. today/yesterday/3 days ago"),
                    Argument("--all", "-a", action="store_true",
                             help="Show both read and unread notifications"),
                    Argument("--count", "-c", action="store", type=int,
                             help="Max number of notifications to show"),
                    Argument("--mark", "-m", action="store_true",
                             help="Mark notifications as seen")],
                   help="Show notifications")]

    COMMANDS = [Command("user", USER),
                Command("post", POST),
                Command("like", LIKE),
                Command("msg", MSG)]

    def __init__(self, args):
        """Command Line Main Entry Point"""
        self.main_parser = CommandLineParser(self.ARGUMENTS, self.COMMANDS)
        self.ns = self.main_parser.parse_args(args)

        # Set some logging details based on the command line args
        shared.DEBUG = self.ns.log_level == logging.DEBUG
        logging.basicConfig(level=self.ns.log_level)
        self.logger = logging.getLogger(__name__)

        # Read config based on command line args, $BSCONFIG or default config file
        config_path = (self.ns.config or
                       os.environ.get("BSCONFIG") or
                       BlueSkyCommandLine.CONFIG_PATH_DEFAULT)
        self.config = self.get_config(config_path)
        self.handle, self._password = (self.config.get("auth", "user"),
                                       self.config.get("auth", "password"))

        # Create the bluesky client that interacts with the BlueSky API
        self.bs = bluesky.BlueSky(self.handle, self._password)

    def run(self):
        """Run the function for the command line given to the constructor"""

        # self.ns is populated when we call CommandLineParser.parse_args() in the
        # constructor. self.ns contains the name of the top level command and
        # the name of the sub-command chosen. For example "user profile". "user" is
        # the top level command and "profile" is the sub-command. The top level
        # command is used to find the class to instantiate (see cmd_name_to_class_name
        # below). The sub-command is used as the method name to invoke on that
        # instantiated object. For "user profile" it would be the "UserCmd" class with
        # its "profile" method. All command classes are derived from BaseCmd which
        # conains the run() method invoked below. run() finds the correct method to
        # handle the chosen command based on the sub-command name given on the
        # command line.
        #
        # self.ns also contains a "func_args" lambda that assembles the function
        # arguments from the parsed command line. It is used in BaseCmd.run() to
        # supply the command line arguments to the method that will handle the
        # sub-command.

        try:
            cls = globals()[self.cmd_name_to_class_name(self.ns.cmd.parent_name)]
        except KeyError:
            self.main_parser.parse_args([self.ns.cmd.name, "-h"])
            sys.exit(1)

        cls(self.bs, self.ns, self.config).run()

    @staticmethod
    def cmd_name_to_class_name(cmd_name):
        """Convert the command name to a class name that handles that command.
           For example: user -> UserCmd, post -> PostCmd"""
        return f"{cmd_name.capitalize()}Cmd"

    @staticmethod
    def get_config(path):
        """Read config data and return"""
        cp = configparser.ConfigParser()
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        cp.read(path)
        return cp


def main():
    """main entrypoint to create and run the command line client"""
    try:
        BlueSkyCommandLine(sys.argv[1:]).run()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)
    except Exception as ex:     # pylint: disable=broad-except
        if shared.DEBUG:
            import traceback    # pylint: disable=import-outside-toplevel
            traceback.print_exc()
        else:
            print(type(ex))
            print(ex)
        sys.exit(1)


if __name__ == "__main__":
    main()
