'''BlueSky class to interact with the Blue Sky API via atproto'''

# pylint: disable=W0511

from datetime import datetime

import atproto
import atproto_core
import atproto_client
import wcwidth
from wand.image import Image

import date


class BlueSky:
    '''Command line client for Blue Sky'''
    BLUESKY_MAX_IMAGE_SIZE = 976.56 * 1024
    FAILURE_LIMIT = 10

    def __init__(self, handle, password):
        self._handle = handle
        self._password = password
        self._client = atproto.Client()
        self._login()

    def get_likes(self, date_limit_str, get_date):
        '''A generator to yield posts that the given user handle has liked'''
        params = {
                "actor": self._handle,
                "limit": 100,
                }
        cursor = None
        date_limit = date.parse(date_limit_str) if date_limit_str else None
        num_failures = 0

        while num_failures < self.FAILURE_LIMIT:
            params['cursor'] = cursor
            try:
                rsp = self._client.app.bsky.feed.get_actor_likes(params=params)
                if not rsp.feed:
                    break

                for like in rsp.feed:
                    if date_limit or get_date:
                        like_rsp = self._client.app.bsky.feed.like.get(
                                      *self.at_uri_to_did_rkey(like.post.viewer.like))
                        like.created_at = like_rsp.value.created_at
                    else:
                        like.created_at = None

                    if date_limit:
                        dt = datetime.strptime(like.created_at,
                                               date.BLUESKY_DATE_FORMAT)
                        if dt < date_limit:
                            return

                    yield like
                if rsp.cursor:
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            # TODO: Convert to verbose log
            print(f"Giving up, more than {self.FAILURE_LIMIT} failures")

    def get_mutuals(self, handle, flag):
        '''A generator to yield entries for users that the given user follows
           and who are also followers of the given user, if flag == both.
           If flag == follows-not-followers yield entries of users that the user
           follows who don't follow back.
           If flag = followers-not-follows yield entries of users that follow
           this user that this user does not follow back'''

        # hmm, I suppose this could be kind of heavyweight
        dfollows = {entry.handle: entry for entry in self.follows(handle)}
        dfollowers = {entry.handle: entry for entry in self.followers(handle)}

        follows = set(dfollows.keys())
        followers = set(dfollowers.keys())

        if flag == 'both':
            for mutual in follows & followers:
                yield dfollows[mutual]
        elif flag == 'follows-not-followers':
            for mutual in follows - followers:
                yield dfollows[mutual]
        elif flag == 'followers-not-follows':
            for mutual in followers - follows:
                yield dfollowers[mutual]
        else:
            raise ValueError(f"Invalid flag: '{flag}'. Expected 'both', "
                             f"'follows-not-followers', or 'followers-not-follows'.")

    def get_reposters(self, handle, date_limit_str=None):
        '''A generator to yield people that have reposts posts for the given user
           handle'''
        repost_info = {}

        for post in self.get_posts(handle, date_limit_str=date_limit_str):
            if post.repost_count:
                reposters = self._client.get_reposted_by(post.uri)
                for profile in reposters.reposted_by:
                    if profile.handle in repost_info:
                        repost_info[profile.handle]['count'] += 1
                    else:
                        repost_info[profile.handle] = {
                                'count': 1,
                                'profile': profile
                        }

        sorted_items = sorted(repost_info.items(),
                              key=lambda item: item[1]['count'], reverse=True)

        for _, info in sorted_items:
            yield info['profile'], info['count']

    def post_text(self, text):
        '''Post the given text and return the resulting post uri'''
        post = self._client.send_post(text)
        return post.uri

    def post_image(self, text, filename, alt):
        '''Post the given image with the given text and given alt-text'''
        img_data = self._get_image_data(filename)

        # Add image aspect ratio to prevent default 1:1 aspect ratio
        # Replace with your desired aspect ratio
        aspect_ratio = atproto.models.AppBskyEmbedDefs.AspectRatio(
                            height=100, width=100)

        rsp = self._client.send_image(text=text,
                                      image=img_data,
                                      image_alt=alt or '',
                                      image_aspect_ratio=aspect_ratio)
        return rsp.uri

    def delete_post(self, uri):
        '''Delete the post at the given uri'''
        rsp = self._client.delete_post(uri)
        return rsp

    def get_profile(self, handle):
        '''Return the profile of the given user handle'''
        return self._client.get_profile(handle)

    def get_post(self, uri):
        '''Get details of the post at the given uri'''
        did, rkey = self.at_uri_to_did_rkey(uri)
        num_failures = 0

        while num_failures < self.FAILURE_LIMIT:
            try:
                rsp = self._client.get_post(rkey, profile_identify=did)
                if rsp:
                    break
            except atproto_client.exceptions.BadRequestError as ex:
                # Could they not just return a 404 like everyone else. FFS.
                if ex.response.content.error == 'RecordNotFound':
                    rsp = None
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            # TODO: Convert to verbose log
            print(f"Giving up, more than {self.FAILURE_LIMIT} failures")
            rsp = None

        return rsp

    def get_unread_notifications_count(self):
        '''Return a count of the unread notifications for the authenticated user'''
        return self._client.app.bsky.notification.get_unread_count()

    def get_notifications(self, date_limit_str=None, count_limit=None,
                          mark_read=False):
        '''A generator to yield notifications for the authenticated handle'''
        date_limit = date.parse(date_limit_str) if date_limit_str else None
        count = 0
        num_failures = 0
        cursor = None

        while num_failures < BlueSky.FAILURE_LIMIT:
            try:
                rsp = self._client.app.bsky.notification.list_notifications(
                        params={'cursor': cursor})
                for notif in rsp.notifications:
                    if date_limit:
                        dt = datetime.strptime(notif.record.created_at,
                                            date.BLUESKY_DATE_FORMAT)
                        if dt < date_limit:
                            # Once we get to notifications older than the date
                            # limit, we assume the rest of the notifications are
                            # older, we're done
                            return

                    if count_limit:
                        count += 1
                        if count > count_limit:
                            return

                    if notif.reason == 'reply':
                        post = self.get_post(notif.record.reply.parent.uri)
                    elif notif.reason in ['like', 'repost']:
                        post = self.get_post(notif.reason_subject)
                    else:
                        post = None

                    yield notif, post

                if rsp.cursor:
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            # TODO: Convert to verbose log
            print(f"Giving up, more than {self.FAILURE_LIMIT} failures")

        if mark_read:
            seen_at = self._client.get_current_time_iso()
            self._client.app.bsky.notification.update_seen({'seen_at': seen_at})

    def search(self, term, author, date_limit_str, sort_order, is_follow, is_follower):
        '''A generator to yield posts that match the given search terms'''
        params = { 'q': term,
                   'limit': 100,
                   'sort': sort_order }
        date_limit = date.parse(date_limit_str) if date_limit_str else None
        if author:
            params['author'] = author
        if date_limit:
            params['since'] = date_limit.strftime('%Y-%m-%dT%H:%M:%SZ')

        if is_follow is None:
            follows = []
        else:
            follows = [entry.handle for entry in self.follows(self._handle)]
        if is_follower is None:
            followers = []
        else:
            followers = [entry.handle for entry in self.followers(self._handle)]

        cursor = None
        num_failures = 0

        while num_failures < self.FAILURE_LIMIT:
            params['cursor'] = cursor
            try:
                rsp = self._client.app.bsky.feed.search_posts(params=params)
                for post in rsp.posts:
                    if is_follow is not None:
                        if (is_follow and post.author.handle not in follows) or \
                           (not is_follow and post.author.handle in follows):
                            continue
                    if is_follower is not None:
                        if (is_follower and post.author.handle not in followers) or \
                           (not is_follower and post.author.handle in followers):
                            continue
                    yield (post, follows, followers)

                if rsp.cursor:
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            # TODO: Convert to verbose log
            print(f"Giving up, more than {self.FAILURE_LIMIT} failures")

    def profile_did(self, handle):
        '''Return the DID for a given user handle'''
        return self.get_profile(handle).did

    @staticmethod
    def at_uri_to_http_url(at_uri):
        '''return the http address of the given at-uri'''
        did, rkey = BlueSky.at_uri_to_did_rkey(at_uri)
        return f"https://bsky.app/profile/{did}/post/{rkey}"

    @staticmethod
    def at_uri_to_did_rkey(at_uri):
        '''return the DID and rkey of the given at-uri'''
        _, _, did, _, rkey = at_uri.split('/')
        return did, rkey

    def follows(self, handle):
        '''A generator to return an entry for each user that the given user
           handle follows'''
        cursor = None
        num_failures = 0

        while num_failures < BlueSky.FAILURE_LIMIT:
            try:
                rsp = self._client.get_follows(handle or self._handle, cursor=cursor)
                yield from rsp.follows
                if rsp.cursor:
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            # TODO: Convert to verbose log
            print(f"Giving up, more than {self.FAILURE_LIMIT} failures")

    def followers(self, handle):
        '''A generator to return an entry for each user that follows the given user
           handle'''
        cursor = None
        num_failures = 0

        while num_failures < BlueSky.FAILURE_LIMIT:
            try:
                rsp = self._client.get_followers(handle or self._handle, cursor=cursor)
                yield from rsp.followers
                if rsp.cursor:
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            # TODO: Convert to verbose log
            print(f"Giving up, more than {self.FAILURE_LIMIT} failures")

    def _login(self):
        self._client.login(self._handle, self._password)
        #self._client.login(self._handle, 'c')

    @staticmethod
    def _ljust(text, length, padding=' '):
        return text + padding * max(0, (length - wcwidth.wcswidth(text)))

    @staticmethod
    def _print_at_protocol_error(ex):
        print(type(ex))
        if 'response' in dir(ex):
            if 'status_code' in dir(ex.response):
                print(f"Status: {ex.response.status_code}")
            if 'content' in dir(ex.response):
                if 'message' in dir(ex.response.content):
                    print(f"Message: {ex.response.content.message}")

    def get_posts(self, handle=None, date_limit_str=None, count_limit=None,
                  reply=False, original=False):
        '''A generator to return an entry for posts for the given user handle'''
        date_limit = date.parse(date_limit_str) if date_limit_str else None
        cursor = None
        actor = handle or self._handle
        count = 0
        num_failures = 0

        while num_failures < BlueSky.FAILURE_LIMIT:
            try:
                feed = self._client.get_author_feed(actor=actor, cursor=cursor)
                for view in feed.feed:
                    if date_limit:
                        dt = datetime.strptime(view.post.record.created_at,
                                               date.BLUESKY_DATE_FORMAT)
                        if dt < date_limit:
                            return
                    if count_limit:
                        count += 1
                        if count > count_limit:
                            return
                    if reply and not view.reply:
                        continue
                    if original and view.reply:
                        continue

                    view.post.reply = view.reply
                    yield view.post

                if feed.cursor:
                    cursor = feed.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            # TODO: Convert to verbose log
            print(f"Giving up, more than {self.FAILURE_LIMIT} failures")

    @staticmethod
    def _get_image_data(filename):
        '''Read the image at the given filename and downsize it to under the
           max size permissible for blue sky'''
        scaler = 0.75
        count = 0

        with Image(filename=filename) as img:
            while count < 100:  # need some limit, surely 100 is enough
                img_data = img.make_blob()
                if len(img_data) < BlueSky.BLUESKY_MAX_IMAGE_SIZE:
                    break

                img.resize(int(img.width * scaler), int(img.height * scaler))
                count += 1

        return img_data
