#!/usr/bin/env python3
"""BlueSky command line interface: User command class"""

import wcwidth
import dateparse
from basecmd import BaseCmd


class UserCmd(BaseCmd):
    """BlueSky command line interface: User command class"""

    def did(self, handle):
        """Print the DID of the given user"""
        hand = handle or self.bs.handle
        if "." not in hand:
            hand += ".bsky.social"
        did = self.bs.profile_did(hand)
        if did:
            print(did)
        else:
            print(f"No DID found for {hand}")

    def profile(self, handle):
        """Print the profile entry of the given user handle"""
        profile = self.bs.get_profile(handle)
        if profile:
            self.print_profile(profile, full=True)
        else:
            print(f"{handle} profile not found")

    def follows(self, handle, full):
        """Print details of the users that the current user follows"""
        for profile in self.bs.follows(handle):
            self.print_profile(profile, full=full)

    def followers(self, handle, full):
        """Print details of the users that follow the current user"""
        for profile in self.bs.followers(handle):
            self.print_profile(profile, full=full)

    def mutuals(self, handle, flag, full):
        """If flag == both print the users that the given user follows and who
           are also followers of the given user
           If flag == follows-not-followers print entries of users that the user
           follows who don't follow back.
           If flag = followers-not-follows print entries of users that follow
           this user that this user does not follow back"""
        for profile in self.bs.get_mutuals(handle, flag):
            self.print_profile(profile, full=full)

    def reposters(self, handle, date_limit, full):
        """Print the user handles of the users that have reposted posts by the
           given user handle. Optionally print the count of times each user has
           reposted the user's posts"""
        total = 0
        for repost_info in self.bs.get_reposters(handle, date_limit):
            if full:
                self.print_profile(repost_info["profile"], full=full)
                for post in repost_info["posts"]:
                    print(f"Post Link: {self.bs.at_uri_to_http_url(post.uri)}")
                total += repost_info["count"]
                print(f"Repost Count: {repost_info["count"]}")
                print()
            else:
                print(f"@{repost_info["profile"].handle}")
        if full:
            print(f"Total Reposts: {total}")

    def likes(self, date_limit, count_limit, show_date, short=False):
        """Print details of the likes submitted by the currently authenticated user,
           optionally limited by the supplied date."""
        for like in self.bs.get_likes(date_limit,
                                      count_limit=count_limit,
                                      get_date=show_date):
            self.print_like(like, short)

    def print_like(self, like, short):
        """Print details of the given like structure"""
        if short:
            print(self.profile_name(like.post.author))
            print(f"Post Link: {self.bs.at_uri_to_http_url(like.post.uri)}")
            text = like.post.record.text.replace("\n", " ")

            if wcwidth.wcswidth(text) < 77:
                print(text)
            else:
                print(f"{text[:77]}...")
        else:
            print(self.profile_name(like.post.author))
            print(self.profile_link(like.post.author))
            # author_profile = self.profile(handle)
            # followers = author_profile.followers_count
            # f"{like.post.author.display_name} ({followers} followers)\n"
            print(f"Post Link: {self.bs.at_uri_to_http_url(like.post.uri)}")
            if like.created_at:
                print(f"Like Date: {dateparse.humanise_date_string(like.created_at)}")
            print(f"Text: {like.post.record.text}")
        print("-----")
