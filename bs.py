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
from blueskyuser import User
from blueskypost import Post
from blueskylike import Like
from blueskymsg import Msg
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
        config = (self.ns.config or
                  os.environ.get("BSCONFIG") or
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
            self.main_parser.parse_args([self.ns.cmd.name, "-h"])
            sys.exit(1)

        cls(self.bs, self.ns).run()

    @staticmethod
    def get_config(path):
        """Read config data and return"""
        cp = configparser.ConfigParser()
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        cp.read(path)
        return cp.get("auth", "user"), cp.get("auth", "password")


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
