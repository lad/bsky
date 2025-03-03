#!/usr/bin/env python3

'''BlueSky command line interface'''

import os
import sys
import argparse
import configparser

import bluesky
import date
import shared


class BlueSkyCommandLine:
    '''A command line client for the BlueSky API'''
    CONFIG_PATH_DEFAULT = os.path.join(os.getcwd(), '.config')

    def __init__(self, args):
        '''Command Line Main Entry Point'''
        self.ns = self.create_parser().parse_args(args)
        shared.VERBOSE = self.ns.verbose
        shared.DEBUG = self.ns.debug

        config = ( self.ns.config or
                   os.environ.get('DBCONFIG') or
                   BlueSkyCommandLine.CONFIG_PATH_DEFAULT )
        self.handle, self._password = BlueSkyCommandLine._get_config(config)
        self.bs = bluesky.BlueSky(self.handle, self._password)

    def run(self):
        '''Run the function for the command line given to the constructor'''
        getattr(self, self.ns.func)(*self.ns.func_args(self.ns))

    def follows_cmd(self, handle, full):
        '''Print details of the users that the current user follows'''
        for profile in self.bs.follows(handle):
            self.print_profile(profile, full)

    def followers_cmd(self, handle, full):
        '''Print details of the users that follow the current user'''
        for profile in self.bs.followers(handle):
            self.print_profile(profile, full)

    def mutuals_cmd(self, handle, flag, full):
        '''If flag == both print the users that the given user follows and who
           are also followers of the given user
           If flag == follows-not-followers print entries of users that the user
           follows who don't follow back.
           If flag = followers-not-follows print entries of users that follow
           this user that this user does not follow back'''
        for profile in self.bs.get_mutuals(handle, flag):
            self.print_profile(profile, full)

    def post_cmd(self, text, show_uri):
        '''Post the given text and optionally print the resulting post uri'''
        uri = self.bs.post_text(text)
        if show_uri:
            print(uri)

    def rich_cmd(self, text, mentions, show_uri):
        uri = self.bs.post_rich(text, mentions)
        if show_uri:
            print(uri)

    def postimage_cmd(self, text, filename, alt, show_uri):
        '''Post the given image with the given text and given alt-text'''
        uri = self.bs.post_image(text, filename, alt)
        if show_uri:
            print(uri)

    def posts_cmd(self, handle, since, count, reply, original):
        '''Print the posts by the given user handle limited by the date and count
           supplied'''
        for post in self.bs.get_posts(handle, since, count, reply, original):
            self.print_post_entry(post)

    def delete_cmd(self, uri):
        '''Delete the post at the given uri'''
        rsp = self.bs.delete_post(uri)
        print(rsp)

    def profile_cmd(self, handle):
        '''Print the profile entry of the given user handle'''
        profile = self.bs.get_profile(handle or self.handle)
        self.print_profile(profile, True)

    def notifications_cmd(self, since, show_all, count_limit, mark):
        '''Print the unread, or all, notifications received, optionally since the
           date supplied. Optionally mark the unread notifications as read'''
        notification_count, unread_count = 0, 0
        for notif, post in self.bs.get_notifications(date_limit_str=since,
                                                     count_limit=count_limit,
                                                     mark_read=mark):
            if show_all or not notif.is_read:
                self.print_notification_entry(notif, post)

            if not notif.is_read:
                unread_count += 1
            notification_count += 1

        print(f"{notification_count} notifications, "
              f"{notification_count - unread_count} read, "
              f"{unread_count} unread")

    def unread_notifications_count_cmd(self):
        '''Print a count of the unread notifications'''
        count = self.bs.get_unread_notifications_count()
        print(f"Unread: {count}")

    def likes_cmd(self, since, show_date):
        '''Print details of the likes submitted by the currently authenticated user,
           optionally limited by the supplied date.'''
        for like in self.bs.get_likes(since, show_date):
            self.print_like(like)

    def reposters_cmd(self, handle, since, full):
        '''Print the user handles of the users that have reposted posts by the
           given user handle. Optionally print the count of times each user has
           reposted the user's posts'''
        total = 0
        for repost_info in self.bs.get_reposters(handle or self.handle, since):
            if full:
                self.print_profile(repost_info['profile'], full)
                for post in repost_info['posts']:
                    print(f"Post Link: {self.bs.at_uri_to_http_url(post.uri)}")
                total += repost_info['count']
                print(f"Repost Count: {repost_info['count']}")
                print()
            else:
                print(f"@{repost_info['profile'].handle}")
        if full:
            print(f"Total Reposts: {total}")

    # Specifies the ranking order of results.
    # until (string)
    #
    # Filter results for posts before the indicated datetime (not inclusive).
    # Expected to use 'sortAt' timestamp, which may not match 'createdAt'. Can be
    # a datetime, or just an ISO date (YYY-MM-DD).
    #
    # mentions (at-identifier)
    #
    # Filter to posts which mention the given account. Handles are resolved to
    # DID before query-time. Only matches rich-text facet mentions.
    #
    #
    # author (at-identifier)
    #
    # Filter to posts by the given account. Handles are resolved to DID before
    # query-time.
    #
    #
    #
    # tag (string[])
    #
    # Possible values: <= 640 characters
    #
    # Filter to posts with the given tag (hashtag), based on rich-text facet or
    # tag field. Do not include the hash (#) prefix. Multiple tags can be
    #                                     specified, with 'AND' matching.
    #
    # limit (integer)
    #
    # Possible values: >= 1 and <= 100
    # Default value: 25

    def search_cmd(self, term, author, since, sort_order, is_follow, is_follower):
        '''Print posts that match the given search terms. Optionally limit the
           search to the supplied date and/or output whether the poster is a
           follower or is followed by the currently authenticated user'''
        for post, follows, followers in self.bs.search(term, author, since, sort_order,
                                                       is_follow, is_follower):
            self.print_post_entry(post, follows=follows, followers=followers)

    def print_like(self, like):
        '''Print details of the given like structure'''
        self.print_profile_name(like.post.author)
        self.print_profile_link(like.post.author)
        # author_profile = self.profile(handle)
        # followers = author_profile.followers_count
        # f"{like.post.author.display_name} ({followers} followers)\n"
        print(f"Post Link: {self.bs.at_uri_to_http_url(like.post.uri)}")
        if like.created_at:
            print(f"Like Date: {date.humanise_date_string(like.created_at)}")
        print(f"Text: {like.post.record.text}")
        print('-----')

    def print_profile(self, profile, full=False):
        '''Print details of the given profile structure'''
        self.print_profile_name(profile)
        if full:
            self.print_profile_link(profile)
            print(f"DID: {profile.did}")
            print(f"Created at: {date.humanise_date_string(profile.created_at)}")
            if profile.description:
                print("Description:  ",
                      profile.description.replace("\n", "\n              "), "\n",
                      sep='')

    @staticmethod
    def print_profile_name(author):
        '''Print the display name of the given profile'''
        print(f"Profile: {author.handle} ({author.display_name})")

    @staticmethod
    def print_profile_link(author):
        '''Print the http link to the profile of the given user'''
        print(f"Profile Link: https://bsky.app/profile/{author.handle}")

    def print_profile_did(self, handle):
        '''Print the DID of the given user'''
        print(self.bs.profile_did(handle or self.handle))

    def print_post_entry(self, post, follows=None, followers=None):
        '''Print details of the given post structure'''
        self.print_profile_name(post.author)
        self.print_profile_link(post.author)
        if follows:
            is_follow = post.author.handle in follows
            print(f"Follows: {is_follow}")
        if followers:
            is_follower = post.author.handle in followers
            print(f"Follower: {is_follower}")
        print(f"Date: {date.humanise_date_string(post.record.created_at)}")
        print(f"Post URI: {post.uri}")
        print(f"Post Link: {self.bs.at_uri_to_http_url(post.uri)}")
        if post.reply:
            print(f"Reply Link: {self.bs.at_uri_to_http_url(post.reply.root.uri)}")
        print(f"Likes: {post.like_count}")
        print(f"Text: {post.record.text}")
        print('-----')

    def print_notification_entry(self, notif, post):
        '''Print details of the given notification structure'''
        self.print_profile_name(notif.author)
        self.print_profile_link(notif.author)
        print(f"Reason: {notif.reason}")
        print(f"Date: {date.humanise_date_string(notif.indexed_at)}")
        if post:
            print(f"Post: {post.value.text}")
        if hasattr(notif.record, 'text'):
            print(f"Reply: {notif.record.text}")
        print('-----')

    @staticmethod
    def _get_config(path):
        '''Read config data and return'''
        cp = configparser.ConfigParser()
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        cp.read(path)
        return cp.get('auth', 'user'), cp.get('auth', 'password')

    def create_parser(self):
        '''Create the top level command parser and attach parsers for sub-commands'''
        main_parser = argparse.ArgumentParser()

        # Global arguments
        main_parser.add_argument('--verbose', '-v', action='store_true')
        main_parser.add_argument('--debug', '-d', action='store_true')
        main_parser.add_argument('--config', '-c', dest='config', action='store',
                                 help='config file or $BSCONFIG or $PWD/.config')

        sub_parser = main_parser.add_subparsers(title='Sub Commands')

        # Get all add parser methods (.add_parser_XXXX)
        methods = [method for method in dir(self)
                   if callable(getattr(self, method))
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
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.set_defaults(func='show_profile_did',
                            func_args=lambda ns: [ns.handle])

    @staticmethod
    def add_parser_follows(parent):
        """Add a sub-parser for the 'follows' command"""
        parser = parent.add_parser('follows', help="show who a user follows")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show more details of each user')
        parser.set_defaults(func='follows_cmd',
                            func_args=lambda ns: [ns.handle, ns.full])

    @staticmethod
    def add_parser_followers(parent):
        """Add a sub-parser for the 'followers' command"""
        parser = parent.add_parser('followers',
                                   help="show the given user's followers")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show more details of each user')
        parser.set_defaults(func='followers_cmd',
                            func_args=lambda ns: [ns.handle, ns.full])

    @staticmethod
    def add_parser_mutuals(parent):
        """Add a sub-parser for the 'mutuals' command"""
        parser = parent.add_parser('mutuals',
                                   help="show who follows the given user")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--flag',
                            choices=['both',
                                     'follows-not-followers', 'followers-not-follows'],
                            default='both',
                            help="both show mutuals, follows-not-followers show "
                                 "users that the given user follows that don't "
                                 "follow back, followers-not-follows show users that "
                                 "follow the given user that the user doesn't follow "
                                 "back")
        parser.add_argument('--full', action='store_true',
                            help='Show more details of each user')
        parser.set_defaults(func='mutuals_cmd',
                            func_args=lambda ns: [ns.handle, ns.flag, ns.full])

    @staticmethod
    def add_parser_post(parent):
        """Add a sub-parser for the 'post' command"""
        parser = parent.add_parser('post', help='post text to BlueSky')
        parser.add_argument('text', action='store', help='text to post')
        parser.add_argument('--uri', '-u', action='store_true',
                            help='Show URI of post')
        parser.set_defaults(func='post_cmd', func_args=lambda ns: [ns.text, ns.uri])

    @staticmethod
    def add_parser_rich(parent):
        """Add a sub-parser for the 'rich' command"""
        parser = parent.add_parser('rich', help='post text to BlueSky')
        parser.add_argument('text', action='store', help='text to post')
        parser.add_argument('--mentions', '-m', nargs='+',
                            help='A list of user mentions (no @ required)')
        parser.add_argument('--uri', '-u', action='store_true',
                            help='Show URI of post')
        parser.set_defaults(func='rich_cmd',
                            func_args=lambda ns: [ns.text, ns.mentions, ns.uri])

    @staticmethod
    def add_parser_posts(parent):
        """Add a sub-parser for the 'posts' command"""
        parser = parent.add_parser('posts', help='show BlueSky posts')
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit (e.g. today/yesterday/3 days ago')
        parser.add_argument('--count', '-c', type=int, action='store',
                            help='Count of posts to display')
        parser.add_argument('handle', nargs='?', help="user's handle")

        group = parser.add_mutually_exclusive_group()
        group.add_argument('--reply', '-r', action='store_true',
                           help='Show replies only')
        group.add_argument('--original', '-o', action='store_true',
                           help='Show original posts only')
        parser.set_defaults(func='posts_cmd',
                            func_args=lambda ns: [ns.handle, ns.since, ns.count,
                                                  ns.reply, ns.original])

    @staticmethod
    def add_parser_post_image(parent):
        """Add a sub-parser for the 'posts_image' command"""
        parser = parent.add_parser('postimage', aliases=['pi'],
                                   help='post image to BlueSky')
        parser.add_argument('text', action='store', help='text to post')
        parser.add_argument('filename', action='store', help='Path to image file')
        parser.add_argument('--alt', '-a', action='store', help='Image alt text')
        parser.add_argument('--uri', '-u', action='store_true',
                            help='Show URI of post')
        parser.set_defaults(func='postimage_cmd',
                            func_args=lambda ns: [ns.text, ns.filename,
                                                  ns.alt, ns.uri])

    @staticmethod
    def add_parser_delete(parent):
        """Add a sub-parser for the 'delete' command"""
        parser = parent.add_parser('delete', aliases=['del'],
                                   help='delete BlueSky post')
        parser.add_argument('uri', action='store', help='URI to delete')
        parser.set_defaults(func='delete_cmd', func_args=lambda ns: [ns.uri])

    @staticmethod
    def add_parser_reposters(parent):
        """Add a sub-parser for the 'reposters' command"""
        parser = parent.add_parser('reposters', help='show repost users')
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit (e.g. today/yesterday/3 days ago')
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show more details of each user')
        parser.set_defaults(func='reposters_cmd',
                            func_args=lambda ns: [ns.handle, ns.since, ns.full])

    @staticmethod
    def add_parser_profile(parent):
        """Add a sub-parser for the 'profile' command"""
        parser = parent.add_parser('profile', help="show user's profile")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.set_defaults(func='profile_cmd', func_args=lambda ns: [ns.handle])

    @staticmethod
    def add_parser_notifications(parent):
        """Add a sub-parser for the 'notifications' command"""
        parser = parent.add_parser('notifications', aliases=['not', 'notif'],
                                   help="show notifications for "
                                        "the authenticated user")
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit (e.g. today/yesterday/3 days ago')
        parser.add_argument('--all', '-a', action='store_true',
                            help='Show both read and unread notifications')
        parser.add_argument('--count', '-c', action='store', type=int,
                            help='Max number of notifications to show')
        parser.add_argument('--mark', '-m', action='store_true',
                            help='Mark notifications as seen')
        parser.set_defaults(func='notifications_cmd',
                            func_args=lambda ns: [ns.since, ns.all, ns.count, ns.mark])

    @staticmethod
    def add_parser_has_unread_notifications(parent):
        """Add a sub-parser for the 'has_unread_notifications' command"""
        parser = parent.add_parser('has_unread_notifications', aliases=['unread'],
                                   help="Show true/false for unread notifications")
        parser.set_defaults(func='unread_notifications_count_cmd',
                            func_args=lambda ns: [])

    @staticmethod
    def add_parser_likes(parent):
        """Add a sub-parser for the 'likes' command"""
        parser = parent.add_parser('likes', help="show likes for authenticated user")
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit (e.g. today/yesterday/3 days ago')
        parser.add_argument('--date', '-d', action='store_true',
                            help='Show date of each like (more costly)')
        parser.set_defaults(func='likes_cmd',
                            func_args=lambda ns: [ns.since, ns.date])

    @staticmethod
    def add_parser_search(parent):
        """Add a sub-parser for the 'search' command"""
        parser = parent.add_parser('search', help="show posts for a given search "
                                                  "string (Lucene search strings "
                                                  "supported)")
        parser.add_argument('term', action='store', help="term to search for")
        parser.add_argument('--author', action='store',
                            help='Restrict result to the given author handle')
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit (e.g. today/yesterday/3 days ago')
        parser.add_argument('--sort', choices=['top', 'latest'],
                            default='top',
                            help="Sort result by top or latest")
        parser.add_argument('--follow', choices=['true', 'false', None],
                            help="Show only posts by users that the authenticated "
                                 "user follows (true) or doesn't follow (false)")
        parser.add_argument('--follower', choices=['true', 'false', None],
                            help='Show only posts by users that are followers '
                                 '(true) or not followers (false) of the '
                                 'authenticated user')
        parser.set_defaults(func='search_cmd',
                            func_args=lambda ns:
                            [ns.term, ns.author, ns.since, ns.sort,
                             BlueSkyCommandLine._true_false(ns.follow),
                             BlueSkyCommandLine._true_false(ns.follower)])

    @staticmethod
    def _true_false(flag):
        '''Check true/false argument string'''
        if flag == 'true':
            return True
        if flag == 'false':
            return False
        return None


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
            print(type(ex))
            print(ex)
        sys.exit(1)


if __name__ == '__main__':
    main()
