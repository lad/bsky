#!/usr/bin/env python3

'''blue sky command line interface'''

import os
import sys
import argparse
import configparser

import bluesky
import shared

CONFIG_PATH_DEFAULT = os.path.join(os.getcwd(), '.config')


class BlueSkyCommandLine:
    '''A command line client for the BlueSky API'''
    def __init__(self, args):
        '''Command Line Main Entry Point'''
        self.ns = self._create_parser().parse_args(args)
        shared.VERBOSE = self.ns.verbose
        shared.DEBUG = self.ns.debug

        config = self.ns.config or os.environ.get('DBCONFIG') or CONFIG_PATH_DEFAULT
        self.user, self.password = BlueSkyCommandLine._get_config(config)

    def run(self):
        '''Run the function for the command line given to the constructor'''
        bs = bluesky.BlueSky(self.user, self.password)
        getattr(bs, self.ns.func)(*self.ns.func_args(self.ns))

    @staticmethod
    def _get_config(path):
        '''Read config data and Return'''
        cp = configparser.ConfigParser()
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        cp.read(path)
        return cp.get('auth', 'user'), cp.get('auth', 'password')

    def _create_parser(self):
        '''Create the top level command parser and attach parsers for sub-commands'''
        main_parser = argparse.ArgumentParser()

        # Global arguments
        main_parser.add_argument('--verbose', '-v', action='store_true')
        main_parser.add_argument('--debug', '-d', action='store_true')
        main_parser.add_argument('--config', '-c', dest='config', action='store',
                                help='config file or $BSCONFIG or $PWD/.config')

        sub_parser = main_parser.add_subparsers(title='Sub Commands')

        # Get all add parser methods (.add_parser_XXXX)
        methods = [method for method in dir(self) \
                   if callable(getattr(self, method)) \
                   if method.startswith('add_parser_')]

        # Invoke these methods
        for method in methods:
            getattr(self, method)(sub_parser)

        # wrap parser.parse_args() to make it act like one sub command is required.
        # No required keyword for sub-parsers until py 3.7
        def parse(args):
            ns = main_parser.original_parse_args(args)
            if not hasattr(ns, 'func'):
                main_parser.print_help()
                sys.exit(1)
            return ns

        main_parser.original_parse_args = main_parser.parse_args
        main_parser.parse_args = parse
        return main_parser

    @staticmethod
    def add_parser_did(parent):
        """Add a sub-parser for the 'did' command"""
        parser = parent.add_parser('did', help="show a user's did")
        parser.add_argument('handle', action='store', help="user's handle")
        parser.set_defaults(func='profile_did', func_args=lambda ns: [ns.handle])

    @staticmethod
    def add_parser_follows(parent):
        """Add a sub-parser for the 'follows' command"""
        parser = parent.add_parser('follows', help="show who a user follows")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show more details of each user')
        parser.set_defaults(func='follows', func_args=lambda ns: [ns.handle, ns.full])

    @staticmethod
    def add_parser_followers(parent):
        """Add a sub-parser for the 'followers' command"""
        parser = parent.add_parser('followers', help="show who follows the given user")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show more details of each user')
        parser.set_defaults(func='followers',
                            func_args=lambda ns: [ns.handle, ns.full])

    @staticmethod
    def add_parser_mutuals(parent):
        """Add a sub-parser for the 'mutuals' command"""
        parser = parent.add_parser('mutuals',
                                help="show who follows the given user")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--flag', '-f',
                            choices=['both',
                                    'follows-not-followers',
                                    'followers-not-follows'],
                            default='both',
            help="both show mutuals, "
                "follows-not-followers show users that the given user follows that "
                "don't follow back, "
                "followers-not-follows show users that follow the given user that "
                "the user doesn't follow back")
        parser.set_defaults(func='mutuals', func_args=lambda ns: [ns.handle, ns.flag])

    @staticmethod
    def add_parser_post(parent):
        """Add a sub-parser for the 'post' command"""
        parser = parent.add_parser('post', help='post text to BlueSky')
        parser.add_argument('text', action='store', help='text to post')
        parser.add_argument('--uri', '-u', action='store_true',
                            help='Show URI of post')
        parser.set_defaults(func='post', func_args=lambda ns: [ns.text, ns.uri])

    @staticmethod
    def add_parser_posts(parent):
        """Add a sub-parser for the 'posts' command"""
        parser = parent.add_parser('posts', help='show BlueSky posts')
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit for posts '
                                 '(e.g. today/yesterday/3 days ago')
        parser.add_argument('--count', '-c', type=int, action='store',
                            help='Count of posts to display')
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.set_defaults(func='posts', func_args=lambda ns: [ns.handle, ns.since,
                                                                ns.count])

    @staticmethod
    def add_parser_post_image(parent):
        """Add a sub-parser for the 'posts_image' command"""
        parser = parent.add_parser('postimage', aliases=['pi'],
                                help='post image to BlueSky')
        parser.add_argument('text', action='store', help='text to post')
        parser.add_argument('filename', action='store', help='Path to image file')
        parser.add_argument('--alt', '-a', action='store', help='Image alt text')
        parser.set_defaults(func='post_image',
                            func_args=lambda ns: [ns.text, ns.filename, ns.alt])

    @staticmethod
    def add_parser_delete(parent):
        """Add a sub-parser for the 'delete' command"""
        parser = parent.add_parser('delete', aliases=['del'],
                                   help='delete BlueSky post')
        parser.add_argument('uri', action='store', help='URI to delete')
        parser.set_defaults(func='delete', func_args=lambda ns: [ns.uri])

    @staticmethod
    def add_parser_reposters(parent):
        """Add a sub-parser for the 'reposters' command"""
        parser = parent.add_parser('reposters', help='show repost users')
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show more details of each user')
        parser.set_defaults(func='reposters',
                            func_args=lambda ns: [ns.handle, ns.full])

    @staticmethod
    def add_parser_profile(parent):
        """Add a sub-parser for the 'profile' command"""
        parser = parent.add_parser('profile', help="show  user's profile")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.set_defaults(func='profile',
                            func_args=lambda ns: [ns.handle])

    @staticmethod
    def add_parser_notifications(parent):
        """Add a sub-parser for the 'notifications' command"""
        parser = parent.add_parser('notifications', help="show notifications for "
                                                         "the authenticated user")
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit for posts '
                                 '(e.g. today/yesterday/3 days ago')
        parser.add_argument('--all', '-a', action='store_true',
                            help='Show both read and unread notifications')
        parser.add_argument('--mark', '-m', action='store_true',
                            help='Mark notifications as seen')
        parser.set_defaults(func='notifications',
                            func_args=lambda ns: [ns.since, ns.all, ns.mark])

    @staticmethod
    def add_parser_likes(parent):
        """Add a sub-parser for the 'likes' command"""
        parser = parent.add_parser('likes', help="show likes for authenticated user")
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit for likes '
                                 '(e.g. today/yesterday/3 days ago')
        parser.add_argument('--date', '-d', action='store_true',
                            help='Show date of each like (more costly)')
        parser.set_defaults(func='likes',
                            func_args=lambda ns: [ns.since, ns.date])


def main():
    '''main entrypoint to create and run the command line client'''
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
            print(ex)
        sys.exit(1)


if __name__ == '__main__':
    main()
