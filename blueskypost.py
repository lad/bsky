#!/usr/bin/env python3
'''BlueSky command line interface: Post command class'''

from blueskycmd import BaseCmd


class Post(BaseCmd):
    '''BlueSky command line interface: Post command class'''

    def get(self, uri, url):
        '''Print details of the post at the given URI or URL'''
        if uri:
            did, rkey = self.bs.at_uri_to_did_rkey(uri)
            profile = self.bs.get_profile(did)
        elif url:
            handle, rkey = self.bs.at_url_to_handle_rkey(url)
            profile = self.bs.get_profile(handle)
            did = profile.did
        else:
            raise ValueError("'uri' or 'url' must be supplied")

        post = self.bs.get_post(did=did, rkey=rkey, likes=True)
        post.author = profile
        if not hasattr(post, 'record'):
            post.record = post.value

        self.print_post_entry(post)

    def gets(self, handle, date_limit_str, count_limit, post_type_filter):
        '''Print the posts by the given user handle limited by the request details
           like: date_limit, count, reply vs. original post'''
        for post in self.bs.get_posts(handle, date_limit_str,
                                      count_limit=count_limit,
                                      post_type_filter=post_type_filter):
            self.print_post_entry(post)

    def put(self, text, show_uri):
        '''Post the given text and optionally print the resulting post uri'''
        uri = self.bs.post_text(text)
        if show_uri:
            print(uri)

    def putr(self, text, mentions, show_uri):
        '''Example command to post using rich text for "mentions"'''
        uri = self.bs.post_rich(text, mentions or [])
        if show_uri:
            print(uri)

    def puti(self, text, filename, alt, show_uri):
        '''Post the given image with the given text and given alt-text'''
        uri = self.bs.post_image(text, filename, alt)
        if show_uri:
            print(uri)

    def likes(self, uri, full):
        '''Print the like details of the given post'''
        for like in self.bs.get_post_likes(uri):
            self.print_like_entry(like, full)

    def delete(self, uri):
        '''Delete the post at the given uri'''
        rsp = self.bs.delete_post(uri)
        print(rsp)

    def search(self, req):
        '''Print posts that match the given search terms. Optionally limit the
           search to the supplied date and/or output whether the poster is a
           follower or is followed by the currently authenticated user'''
        for post, follows, followers in self.bs.search(req.term, req.author,
                                                       req.date_limit, req.sort_order,
                                                       req.is_follow, req.is_follower):
            self.print_post_entry(post, follows=follows, followers=followers)
