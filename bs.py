#!/usr/bin/env python3

'''BlueSky command line interface'''

import os
import sys
import argparse
import configparser
import logging
from dataclasses import dataclass

import wcwidth

import bluesky
import dateparse
import shared


@dataclass
class PostsCommandRequest:
    '''Encapsulate fields to represent a query about posts'''
    handle: str
    date_limit: str
    count_limit: int
    post_type_filter: bluesky.PostTypeMask
    full: bool = False


@dataclass
class SearchCommandRequest:
    '''Encapsulate fields to represent a search query command'''
    term: str
    author: str
    date_limit: str
    sort_order: str
    is_follow: bool
    is_follower: bool


class CommandLineParser:
    '''Parser for BlueSkyCommandLine'''
    def __init__(self, args):
        self.args = args
        self.main_parser = self.create_parser()

    def parse_args(self):
        '''Parse command line arguments and return namespace results'''
        return self.main_parser.parse_args(self.args)

    def create_parser(self):
        '''Create the top level command parser and attach parsers for sub-commands'''
        main_parser = argparse.ArgumentParser()

        # Global arguments
        main_parser.add_argument('--critical', action='store_true',
                                 help='Set log level to CRITICAL')
        main_parser.add_argument('--error', '-e', action='store_true',
                                 help='Set log level to ERROR')
        main_parser.add_argument('--warning', '-w', action='store_true',
                                 help='Set log level to WARNING')
        main_parser.add_argument('--info', '-i', action='store_true',
                                 help='Set log level to INFO')
        main_parser.add_argument('--debug', '-d', action='store_true',
                                 help='Set log level to DEBUG')
        main_parser.add_argument('--verbose', '-v', action='store_true',
                                 help='Synonym for --debug')
        main_parser.add_argument('--config', '-c', dest='config', action='store',
                                 help='config file or $BSCONFIG or $PWD/.config')

        sub_parser = main_parser.add_subparsers(title='Sub Commands')

        # Get all add parser methods (.add_parser_XXXX)
        methods = [method for method in dir(self)
                   if callable(getattr(self, method))
                   if method.startswith('_add_parser_')]

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
    def _add_parser_did(parent):
        """Add a sub-parser for the 'did' command"""
        parser = parent.add_parser('did', help="show a user's did")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.set_defaults(func='did_cmd',
                            func_args=lambda ns: [ns.handle])

    @staticmethod
    def _add_parser_follows(parent):
        """Add a sub-parser for the 'follows' command"""
        parser = parent.add_parser('follows', help="show who a user follows")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show more details of each user')
        parser.set_defaults(func='follows_cmd',
                            func_args=lambda ns: [ns.handle, ns.full])

    @staticmethod
    def _add_parser_followers(parent):
        """Add a sub-parser for the 'followers' command"""
        parser = parent.add_parser('followers',
                                   help="show the given user's followers")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show more details of each user')
        parser.set_defaults(func='followers_cmd',
                            func_args=lambda ns: [ns.handle, ns.full])

    @staticmethod
    def _add_parser_mutuals(parent):
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
    def _add_parser_post(parent):
        """Add a sub-parser for the 'post' command"""
        parser = parent.add_parser('post', help='post text to BlueSky')
        parser.add_argument('text', action='store', help='text to post')
        parser.add_argument('--uri', '-u', action='store_true',
                            help='Show URI of post')
        parser.set_defaults(func='post_cmd', func_args=lambda ns: [ns.text, ns.uri])

    @staticmethod
    def _add_parser_rich(parent):
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
    def _add_parser_posts(parent):
        """Add a sub-parser for the 'posts' command"""
        parser = parent.add_parser('posts', help='show BlueSky posts')
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit (e.g. today/yesterday/3 days ago')
        parser.add_argument('--count', '-c', type=int, action='store',
                            help='Count of posts to display')
        parser.add_argument('handle', nargs='?', help="user's handle")

        parser.add_argument('--original', '-o', action='store_true',
                            help='Show original posts only')
        parser.add_argument('--repost', action='store_true',
                            help='Show reposts only')
        parser.add_argument('--reply', action='store_true',
                            help='Show replies only')
        parser.add_argument('--all', '-a', action='store_true',
                            help='Show all posts types')

        parser.set_defaults(func='posts_cmd', func_args=lambda ns:
                            [PostsCommandRequest(
                                ns.handle, ns.since, ns.count,
                                CommandLineParser._options_to_post_types(
                                    ns.original, ns.repost, ns.reply, ns.all))])

    @staticmethod
    def _add_parser_post_image(parent):
        """Add a sub-parser for the 'posts_image' command"""
        parser = parent.add_parser('postimage', aliases=['pi'],
                                   help='post image to BlueSky')
        parser.add_argument('text', action='store', help='text to post')
        parser.add_argument('filename', action='store', help='Path to image file')
        parser.add_argument('--alt', '-a', action='store', help='Image alt text')
        parser.add_argument('--uri', '-u', action='store_true',
                            help='Show URI of post')
        parser.set_defaults(func='post_image_cmd',
                            func_args=lambda ns: [ns.text, ns.filename,
                                                  ns.alt, ns.uri])

    @staticmethod
    def _add_parser_post_likes(parent):
        """Add a sub-parser for the 'posts_likes' command"""
        parser = parent.add_parser('postlikes', aliases=['pl'],
                                   help='Show like details of a particular post')
        parser.add_argument('uri', action='store', help='post URI')
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show full details of each user who likes the post')
        parser.set_defaults(func='post_likes_cmd',
                            func_args=lambda ns: [ns.uri, ns.full])

    @staticmethod
    def _add_parser_posts_likes(parent):
        """Add a sub-parser for the 'postslikes' command"""
        parser = parent.add_parser('postslikes', aliases=['psl'],
                                   help='Show like details of the found posts')
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit (e.g. today/yesterday/3 days ago')
        parser.add_argument('--count', '-c', type=int, action='store',
                            help='Count of posts to display')
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show full details of each user who likes the post')

        parser.add_argument('--original', '-o', action='store_true',
                            help='Show original posts only')
        parser.add_argument('--repost', action='store_true',
                            help='Show reposts only')
        parser.add_argument('--reply', action='store_true',
                            help='Show replies only')
        parser.add_argument('--all', '-a', action='store_true',
                            help='Show all posts types')

        parser.set_defaults(func='posts_likes_cmd', func_args=lambda ns: [
                            PostsCommandRequest(
                                ns.handle, ns.since, ns.count,
                                CommandLineParser._options_to_post_types(
                                    ns.original, ns.repost, ns.reply, ns.all),
                                ns.full)])

    @staticmethod
    def _add_parser_most_likes(parent):
        """Add a sub-parser for the 'mostlikes' command"""
        parser = parent.add_parser(
                    'mostlikes', aliases=['ml'],
                    help='Find users with the most likes for the given posts')
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit (e.g. today/yesterday/3 days ago')
        parser.add_argument('--count', '-c', type=int, action='store',
                            help='Count of posts to display')
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.add_argument('--full', '-f', action='store_true',
                            help='Show full details of each user who likes the post')

        parser.add_argument('--original', '-o', action='store_true',
                            help='Show original posts only')
        parser.add_argument('--repost', action='store_true',
                            help='Show reposts only')
        parser.add_argument('--reply', action='store_true',
                            help='Show replies only')
        parser.add_argument('--all', '-a', action='store_true',
                            help='Show all posts types')
        parser.set_defaults(func='most_likes_cmd', func_args=lambda ns: [
                            PostsCommandRequest(
                                ns.handle, ns.since, ns.count,
                                CommandLineParser._options_to_post_types(
                                    ns.original, ns.repost, ns.reply, ns.all),
                                ns.full)])

    @staticmethod
    def _add_parser_delete(parent):
        """Add a sub-parser for the 'delete' command"""
        parser = parent.add_parser('delete', aliases=['del'],
                                   help='delete BlueSky post')
        parser.add_argument('uri', action='store', help='URI to delete')
        parser.set_defaults(func='delete_cmd', func_args=lambda ns: [ns.uri])

    @staticmethod
    def _add_parser_reposters(parent):
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
    def _add_parser_profile(parent):
        """Add a sub-parser for the 'profile' command"""
        parser = parent.add_parser('profile', help="show user's profile")
        parser.add_argument('handle', nargs='?', help="user's handle")
        parser.set_defaults(func='profile_cmd', func_args=lambda ns: [ns.handle])

    @staticmethod
    def _add_parser_notifications(parent):
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
    def _add_parser_has_unread_notifications(parent):
        """Add a sub-parser for the 'has_unread_notifications' command"""
        parser = parent.add_parser('has_unread_notifications', aliases=['unread'],
                                   help="Show true/false for unread notifications")
        parser.set_defaults(func='unread_notifications_count_cmd',
                            func_args=lambda ns: [])

    @staticmethod
    def _add_parser_likes(parent):
        """Add a sub-parser for the 'likes' command"""
        parser = parent.add_parser('likes', help="show likes for authenticated user")
        parser.add_argument('--since', '-s', action='store',
                            help='Date limit (e.g. today/yesterday/3 days ago')
        parser.add_argument('--count', '-c', action='store', type=int,
                            help='Max number of notifications to show')
        parser.add_argument('--date', '-d', action='store_true',
                            help='Show date of each like (more costly)')
        parser.add_argument('--short',  action='store_true',
                            help='Show a short format output')
        parser.set_defaults(func='likes_cmd',
                            func_args=lambda ns: [ns.since, ns.count,
                                                  ns.date, ns.short])

    @staticmethod
    def _add_parser_search(parent):
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
                            [SearchCommandRequest(
                                ns.term, ns.author, ns.since, ns.sort,
                                CommandLineParser._true_false(ns.follow),
                                CommandLineParser._true_false(ns.follower))])

    @staticmethod
    def _true_false(flag):
        '''Check true/false argument string'''
        if flag == 'true':
            return True
        if flag == 'false':
            return False
        return None

    @staticmethod
    def _options_to_post_types(original, repost, reply, allposts):
        typ = 0
        if original:
            typ |= bluesky.PostTypeMask.ORIGINAL
        if repost:
            typ |= bluesky.PostTypeMask.REPOST
        if reply:
            typ |= bluesky.PostTypeMask.REPLY
        if allposts:
            typ |= bluesky.PostTypeMask.ALL
        if typ == 0:
            # Default if no post type options are given
            typ = bluesky.PostTypeMask.ORIGINAL
        return bluesky.PostTypeMask(typ)


class BlueSkyCommandLine:
    '''A command line client for the BlueSky API'''
    CONFIG_PATH_DEFAULT = os.path.join(os.getcwd(), '.config')

    def __init__(self, args):
        '''Command Line Main Entry Point'''
        self.ns = CommandLineParser(args).parse_args()
        shared.DEBUG = self.ns.debug
        self.logger = self._configure_logging(self.ns)

        config = (self.ns.config or
                  os.environ.get('DBCONFIG') or
                  BlueSkyCommandLine.CONFIG_PATH_DEFAULT)
        self.handle, self._password = BlueSkyCommandLine._get_config(config)
        self.bs = bluesky.BlueSky(self.handle, self._password)

    def _configure_logging(self, ns):
        if ns.critical:
            level = logging.CRITICAL
        elif ns.error:
            level = logging.ERROR
        elif ns.info:
            level = logging.INFO
        elif ns.debug or ns.verbose:
            level = logging.DEBUG
        else:
            # Defaut to warning if no choice given
            level = logging.WARNING

        logging.basicConfig(level=level)
        return logging.getLogger(__name__)

    def run(self):
        '''Run the function for the command line given to the constructor'''
        getattr(self, self.ns.func)(*self.ns.func_args(self.ns))

    def follows_cmd(self, handle, full):
        '''Print details of the users that the current user follows'''
        for profile in self.bs.follows(handle):
            self._print_profile(profile, full=full)

    def followers_cmd(self, handle, full):
        '''Print details of the users that follow the current user'''
        for profile in self.bs.followers(handle):
            self._print_profile(profile, full=full)

    def mutuals_cmd(self, handle, flag, full):
        '''If flag == both print the users that the given user follows and who
           are also followers of the given user
           If flag == follows-not-followers print entries of users that the user
           follows who don't follow back.
           If flag = followers-not-follows print entries of users that follow
           this user that this user does not follow back'''
        for profile in self.bs.get_mutuals(handle, flag):
            self._print_profile(profile, full=full)

    def post_cmd(self, text, show_uri):
        '''Post the given text and optionally print the resulting post uri'''
        uri = self.bs.post_text(text)
        if show_uri:
            print(uri)

    def rich_cmd(self, text, mentions, show_uri):
        '''Example command to post using rich text for "mentions"'''
        uri = self.bs.post_rich(text, mentions)
        if show_uri:
            print(uri)

    def post_image_cmd(self, text, filename, alt, show_uri):
        '''Post the given image with the given text and given alt-text'''
        uri = self.bs.post_image(text, filename, alt)
        if show_uri:
            print(uri)

    def posts_cmd(self, req):
        '''Print the posts by the given user handle limited by the request details
           like: date_limit, count, reply vs. original post'''
        for post in self.bs.get_posts(req.handle, req.date_limit,
                                      count_limit=req.count_limit,
                                      post_type_filter=req.post_type_filter):
            self._print_post_entry(post)

    def post_likes_cmd(self, uri, full):
        '''Print the like details of the given post'''
        for like in self.bs.get_post_likes(uri):
            self._print_like_entry(like, full)

    def posts_likes_cmd(self, req):
        '''Print the like details of the posts found by the request details
           like: date_limit, count, reply vs. original post'''
        count = 0
        # Don't pass count limit to .get_posts() use count_limit to count the
        # number of liked posts. This could potentially retrieve many posts if
        # there are a lot of posts without any likes.
        for post in self.bs.get_posts(req.handle,
                                      date_limit_str=req.date_limit,
                                      count_limit=None,
                                      post_type_filter=req.post_type_filter):
            if post.like_count:
                count += 1
                for like in self.bs.get_post_likes(post.uri):
                    self._print_like_entry(like, req.full)
                    if req.full:
                        self._print_post_entry(post)

            if req.count_limit and count >= req.count_limit:
                break

    def most_likes_cmd(self, req):
        '''Print details of who most likes the posts found by the given parameters'''
        likes = {}
        for post in self.bs.get_posts(req.handle, req.date_limit,
                                      count_limit=req.count_limit,
                                      post_type_filter=req.post_type_filter):
            for like in self.bs.get_post_likes(post.uri):
                if like.actor.did in likes:
                    count, profile = likes[like.actor.did]
                    count += 1
                    likes[like.actor.did] = count, profile
                else:
                    likes[like.actor.did] = 1, like.actor

        for value in sorted(likes.values(), key=lambda v: v[0], reverse=True):
            if req.full:
                count, profile = value
                print(f"Like Count: {count}")
                self._print_profile(profile, full=True)
            else:
                count, profile = value
                print(f"{count} {profile.handle} ({profile.display_name})")

    def delete_cmd(self, uri):
        '''Delete the post at the given uri'''
        rsp = self.bs.delete_post(uri)
        print(rsp)

    def profile_cmd(self, handle):
        '''Print the profile entry of the given user handle'''
        profile = self.bs.get_profile(handle)
        if profile:
            self._print_profile(profile, full=True)
        else:
            print(f"{handle} profile not found")

    def notifications_cmd(self, date_limit, show_all, count_limit, mark):
        '''Print the unread, or all, notifications received, optionally since the
           date supplied. Optionally mark the unread notifications as read'''
        notification_count, unread_count = 0, 0
        for notif, post in self.bs.get_notifications(date_limit_str=date_limit,
                                                     count_limit=count_limit,
                                                     mark_read=mark, get_all=show_all):
            if show_all or not notif.is_read:
                self._print_notification_entry(notif, post)

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

    def likes_cmd(self, date_limit, count_limit, show_date, short=False):
        '''Print details of the likes submitted by the currently authenticated user,
           optionally limited by the supplied date.'''
        for like in self.bs.get_likes(date_limit,
                                      count_limit=count_limit,
                                      get_date=show_date):
            self._print_like(like, short)

    def reposters_cmd(self, handle, date_limit, full):
        '''Print the user handles of the users that have reposted posts by the
           given user handle. Optionally print the count of times each user has
           reposted the user's posts'''
        total = 0
        for repost_info in self.bs.get_reposters(handle or self.handle, date_limit):
            if full:
                self._print_profile(repost_info['profile'], full=full)
                for post in repost_info['posts']:
                    print(f"Post Link: {self.bs.at_uri_to_http_url(post.uri)}")
                total += repost_info['count']
                print(f"Repost Count: {repost_info['count']}")
                print()
            else:
                print(f"@{repost_info['profile'].handle}")
        if full:
            print(f"Total Reposts: {total}")

    def search_cmd(self, req):
        '''Print posts that match the given search terms. Optionally limit the
           search to the supplied date and/or output whether the poster is a
           follower or is followed by the currently authenticated user'''
        for post, follows, followers in self.bs.search(req.term, req.author,
                                                       req.date_limit, req.sort_order,
                                                       req.is_follow, req.is_follower):
            self._print_post_entry(post, follows=follows, followers=followers)

    def _print_like(self, like, short):
        '''Print details of the given like structure'''
        if short:
            self._print_profile_name(like.post.author)
            print(f"Post Link: {self.bs.at_uri_to_http_url(like.post.uri)}")
            text = like.post.record.text.replace("\n", " ")

            if wcwidth.wcswidth(text) < 77:
                print(text)
            else:
                print(f"{text[:77]}...")
        else:
            self._print_profile_name(like.post.author)
            self._print_profile_link(like.post.author)
            # author_profile = self.profile(handle)
            # followers = author_profile.followers_count
            # f"{like.post.author.display_name} ({followers} followers)\n"
            print(f"Post Link: {self.bs.at_uri_to_http_url(like.post.uri)}")
            if like.created_at:
                print(f"Like Date: {dateparse.humanise_date_string(like.created_at)}")
            print(f"Text: {like.post.record.text}")
        print('-----')

    def _print_profile(self, profile, label='Profile', full=False):
        '''Print details of the given profile structure'''
        self._print_profile_name(profile, label)
        if full:
            self._print_profile_link(profile)
            print(f"DID: {profile.did}")
            print(f"Created at: {dateparse.humanise_date_string(profile.created_at)}")
            if profile.description:
                print("Description:  ",
                      profile.description.replace("\n", "\n              "), "\n",
                      sep='')

    @staticmethod
    def _print_profile_name(author, label='Profile'):
        '''Print the display name of the given profile'''
        if author.display_name:
            display_name = f"{author.display_name} "
        else:
            display_name = ''
        print(f"{label}: {display_name}@{author.handle}")

    @staticmethod
    def _print_profile_link(author):
        '''Print the http link to the profile of the given user'''
        print(f"Profile Link: https://bsky.app/profile/{author.handle}")

    def did_cmd(self, handle):
        '''Print the DID of the given user'''
        hand = handle or self.handle
        if '.' not in hand:
            hand += '.bsky.social'
        print(self.bs.profile_did(hand))

    def _print_post_entry(self, post, follows=None, followers=None):
        '''Print details of the given post structure'''
        self._print_profile_name(post.author)
        self._print_profile_link(post.author)
        if follows:
            is_follow = post.author.handle in follows
            print(f"Follows: {is_follow}")
        if followers:
            is_follower = post.author.handle in followers
            print(f"Follower: {is_follower}")
        print(f"Date: {dateparse.humanise_date_string(post.record.created_at)}")
        if hasattr(post, 'repost_date'):
            print(f"Repost Date: "
                  f"{dateparse.humanise_date_string(post.repost_date)}")
        print(f"Post URI: {post.uri}")
        print(f"Post Link: {self.bs.at_uri_to_http_url(post.uri)}")
        if hasattr(post, 'reply') and post.reply:
            print(f"Reply Link: {self.bs.at_uri_to_http_url(post.reply.root.uri)}")
        print(f"Likes: {post.like_count}")
        print(f"Text: {post.record.text}")
        print('-----')

    def _print_like_entry(self, like, full=False):
        '''Print details of the given post like'''
        self._print_profile(like.actor, label='Liked By', full=full)

    def _print_notification_entry(self, notif, post):
        '''Print details of the given notification structure'''
        self._print_profile_name(notif.author)
        self._print_profile_link(notif.author)
        print(f"Reason: {notif.reason}")
        print(f"Date: {dateparse.humanise_date_string(notif.indexed_at)}")
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
