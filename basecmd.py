#!/usr/bin/env python3
"""BlueSky command line interface: Base class for command classes"""

import dateparse


class BaseCmd:
    """Base command for class which implement command line functions"""

    def __init__(self, bs, ns, config):
        self.bs = bs
        self.ns = ns
        self.config = config

    def run(self):
        """Run the command for the given command details passed to constructor"""
        method_name = self.ns.cmd.name.replace("-", '_')
        getattr(self, method_name)(*self.ns.cmd.func_args(self.ns))

    def print_profile(self, profile, label="Profile", full=False):
        """Print details of the given profile structure"""
        print(self.profile_name(profile, label))
        if full:
            print(self.profile_link(profile))
            print(f"DID: {profile.did}")
            print(f"Created at: {dateparse.humanise_date_string(profile.created_at)}")
            if profile.description:
                print("Description:  ",
                      profile.description.replace("\n", "\n              "), "\n",
                      sep="")

    @staticmethod
    def profile_name(author, label="Profile"):
        """Print the display name of the given profile"""
        if author.display_name:
            display_name = f"{author.display_name} "
        else:
            display_name = ""
        return f"{label}: {display_name}@{author.handle}"

    @staticmethod
    def profile_link(author):
        """Print the http link to the profile of the given user"""
        return f"Profile Link: https://bsky.app/profile/{author.handle}"

    def print_post_entry(self, post, follows=None, followers=None):
        """Print details of the given post structure"""
        print(self.profile_name(post.author))
        print(self.profile_link(post.author))
        if follows:
            is_follow = post.author.handle in follows
            print(f"Follows: {is_follow}")
        if followers:
            is_follower = post.author.handle in followers
            print(f"Follower: {is_follower}")
        print(f"Date: {dateparse.humanise_date_string(post.record.created_at)}")
        if hasattr(post, "repost_date"):
            print(f"Repost Date: "
                  f"{dateparse.humanise_date_string(post.repost_date)}")
        print(f"Post URI: {post.uri}")
        print(f"Post Link: {self.bs.at_uri_to_http_url(post.uri)}")
        if hasattr(post, "reply") and post.reply:
            print(f"Reply Link: {self.bs.at_uri_to_http_url(post.reply.root.uri)}")
        print(f"Likes: {post.like_count}")
        print(f"Text: {post.record.text}")
        print("-----")

    def print_like_entry(self, like, full=False):
        """Print details of the given post like"""
        self.print_profile(like.actor, label="Liked By", full=full)
