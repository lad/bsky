#!/usr/bin/env python3
'''BlueSky command line interface: Like command class'''

# pylint: disable=R0913 (too-many-arguments)
# pylint: disable=R0917 (too-many-positional-arguments)

from blueskycmd import BaseCmd


class Like(BaseCmd):
    '''BlueSky command line interface: Like command class'''

    def get(self, uri, count, no_details, full):
        '''Print the like details of the given post'''
        likes = list(self.bs.get_post_likes(uri))
        if count:
            print(f"Count: {len(likes)}")
        if not no_details:
            for like in likes:
                self.print_like_entry(like, full)

    def gets(self, handle, date_limit_str, count_limit, post_type_filter, full):
        '''Print the like details of the posts found by the request details
           like: date_limit, count, reply vs. original post'''
        count = 0
        # Don't pass count limit to .get_posts() use count_limit to count the
        # number of liked posts. This could potentially retrieve many posts if
        # there are a lot of posts without any likes.

        # TODO: Should the date_limit_str apply to the likes rather than the posts?
        for post in self.bs.get_posts(handle,
                                      date_limit_str=date_limit_str,
                                      count_limit=None,
                                      post_type_filter=post_type_filter):
            if post.like_count:
                count += 1
                for like in self.bs.get_post_likes(post.uri):
                    self.print_like_entry(like, full)
                    if full:
                        self.print_post_entry(post)

            if count_limit and count >= count_limit:
                break

    def most(self, handle, date_limit_str, count_limit, post_type_filter, full):
        '''Print details of who most likes the posts found by the given parameters'''
        likes = {}
        for post in self.bs.get_posts(handle, date_limit_str,
                                      count_limit=count_limit,
                                      post_type_filter=post_type_filter):
            for like in self.bs.get_post_likes(post.uri):
                if like.actor.did in likes:
                    count, profile = likes[like.actor.did]
                    count += 1
                    likes[like.actor.did] = count, profile
                else:
                    likes[like.actor.did] = 1, like.actor

        for value in sorted(likes.values(), key=lambda v: v[0], reverse=True):
            if full:
                count, profile = value
                print(f"Like Count: {count}")
                self.print_profile(profile, full=True)
            else:
                count, profile = value
                print(f"{count} {profile.handle} ({profile.display_name})")
