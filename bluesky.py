'''BlueSky class to interact with the Blue Sky API via atproto'''

# pylint: disable=W0511

from datetime import datetime
import functools
import inspect
import logging

import atproto
import atproto_core
import atproto_client
from wand.image import Image

import dateparse

# pylint: disable=R0912,R0913,R0914,R0917,R0904
# Ignore pylint peevishness. These kinds of restrictions are what ruined many
# python and ruby codebases.


def normalize_handle(func):
    '''Decorator to normalize a handle argument'''
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Get method signature and bind the given arguments to it
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)

        # Assume we have a 'handle' argument and replace with its normalized value
        handle = bound_args.arguments['handle']
        bound_args.arguments['handle'] = self.normalize_handle_value(handle)

        # Call the original wrapped method
        return func(*bound_args.args, **bound_args.kwargs)
    return wrapper


class BlueSky:
    '''Command line client for Blue Sky'''
    BLUESKY_MAX_IMAGE_SIZE = 976.56 * 1024
    FAILURE_LIMIT = 10
    PROFILE_URL = 'https://bsky.app/profile/'

    def __init__(self, handle, password):
        self.handle = handle
        self._password = password
        self.logger = logging.getLogger(__name__)
        self.client = atproto.Client()
        self._login()

    def get_likes(self, date_limit_str, count_limit=None, get_date=False):
        '''A generator to yield posts that the given user handle has liked'''
        params = {
                "actor": self.handle,
                "limit": 100,
                }
        cursor = None
        date_limit = dateparse.parse(date_limit_str) if date_limit_str else None
        num_failures = 0
        count = 0

        while num_failures < self.FAILURE_LIMIT:
            params['cursor'] = cursor
            try:
                rsp = self.client.app.bsky.feed.get_actor_likes(params=params)
                if not rsp.feed:
                    break

                for like in rsp.feed:
                    if date_limit or get_date:
                        like_rsp = self.client.app.bsky.feed.like.get(
                                      *self.at_uri_to_did_rkey(like.post.viewer.like))
                        like.created_at = like_rsp.value.created_at
                    else:
                        like.created_at = None

                    if date_limit:
                        dt = datetime.strptime(like.created_at,
                                               dateparse.BLUESKY_DATE_FORMAT)
                        if dt < date_limit:
                            self.logger.info('Date limit reached')
                            return []

                    if count_limit:
                        count += 1
                        if count > count_limit:
                            self.logger.info('Count limit reached')
                            return []

                    yield like

                if rsp.cursor:
                    self.logger.info('Cursor found, retrieving next page...')
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            self.logger.error("Giving up, more than %s failures", self.FAILURE_LIMIT)

        return []

    @normalize_handle
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

    @normalize_handle
    def get_reposters(self, handle, date_limit_str=None):
        '''A generator to yield people that have reposts posts for the given user
           handle'''
        repost_info = {}

        for post in self.get_posts(handle, date_limit_str=date_limit_str):
            if post.repost_count:
                reposters = self.client.get_reposted_by(post.uri)
                for profile in reposters.reposted_by:
                    if profile.handle in repost_info:
                        repost_info[profile.handle]['count'] += 1
                        repost_info[profile.handle]['posts'].append(post)
                    else:
                        repost_info[profile.handle] = {
                                'count': 1,
                                'profile': profile,
                                'posts': [post]
                        }

        sorted_items = sorted(repost_info.values(),
                              key=lambda item: item['count'], reverse=True)

        yield from sorted_items

    def post_text(self, text):
        '''Post the given text and return the resulting post uri'''
        post = self.client.send_post(text)
        return post.uri

    def post_rich(self, text, mentions):
        '''Post the given text with the given user handle mentions'''
        tb = atproto.client_utils.TextBuilder()
        tb.text(f"{text}\n")
        for handle in mentions:
            tb.mention(f"@{handle}", self.profile_did(handle))
            tb.text("\n")
        post = self.client.send_post(tb)
        return post.uri

    def post_image(self, text, filename, alt):
        '''Post the given image with the given text and given alt-text'''
        img_data = self._get_image_data(filename)

        # Add image aspect ratio to prevent default 1:1 aspect ratio
        # Replace with your desired aspect ratio
        aspect_ratio = atproto.models.AppBskyEmbedDefs.AspectRatio(
                            height=100, width=100)

        self.logger.info('Posting image...')
        rsp = self.client.send_image(text=text,
                                     image=img_data,
                                     image_alt=alt or '',
                                     image_aspect_ratio=aspect_ratio)
        return rsp.uri

    def delete_post(self, uri):
        '''Delete the post at the given uri'''
        num_failures = 0

        while num_failures < self.FAILURE_LIMIT:
            try:
                rsp = self.client.delete_post(uri)
                if rsp:
                    break
                num_failures += 1
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            self.logger.error("Giving up, more than %s failures", self.FAILURE_LIMIT)
            rsp = False

        return rsp

    @normalize_handle
    def get_profile(self, handle):
        '''Return the profile of the given user handle'''
        return self.client.get_profile(handle)

    def get_post(self, uri):
        '''Get details of the post at the given uri'''
        did, rkey = self.at_uri_to_did_rkey(uri)
        num_failures = 0

        while num_failures < self.FAILURE_LIMIT:
            try:
                rsp = self.client.get_post(rkey, profile_identify=did)
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
            self.logger.error("Giving up, more than %s failures", self.FAILURE_LIMIT)
            rsp = None

        return rsp

    @normalize_handle
    def get_posts(self, handle=None, date_limit_str=None, count_limit=None,
                  reply=False, original=False):
        '''A generator to return an entry for posts for the given user handle'''
        date_limit = dateparse.parse(date_limit_str) if date_limit_str else None
        cursor = None
        count = 0
        num_failures = 0

        while num_failures < BlueSky.FAILURE_LIMIT:
            try:
                feed = self.client.get_author_feed(actor=handle, cursor=cursor)
                for view in feed.feed:
                    if date_limit:
                        dt = datetime.strptime(view.post.record.created_at,
                                               dateparse.BLUESKY_DATE_FORMAT)
                        if dt < date_limit:
                            self.logger.info('Date limit reached')
                            return
                    if reply and not view.reply:
                        continue
                    if original and view.reply:
                        continue

                    # Apply count check after filter checks above.
                    if count_limit:
                        count += 1
                        if count > count_limit:
                            self.logger.info('Count limit reached')
                            return

                    view.post.reply = view.reply
                    yield view.post

                if feed.cursor:
                    self.logger.info('Cursor found, retrieving next page...')
                    cursor = feed.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            self.logger.error("Giving up, more than %s failures", self.FAILURE_LIMIT)

    def get_post_likes(self, uri):
        '''A generator to yield details of the likes for a given post uri'''
        cursor = None
        num_failures = 0

        while num_failures < BlueSky.FAILURE_LIMIT:
            try:
                rsp = self.client.get_likes(uri, cursor=cursor)

                yield from rsp.likes
                if rsp.cursor:
                    self.logger.info('Cursor found, retrieving next page...')
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            self.logger.error("Giving up, more than %s failures", self.FAILURE_LIMIT)

    def get_unread_notifications_count(self):
        '''Return a count of the unread notifications for the authenticated user'''
        return self.client.app.bsky.notification.get_unread_count()

    def get_notifications(self, date_limit_str=None, count_limit=None,
                          mark_read=False):
        '''A generator to yield notifications for the authenticated handle'''
        date_limit = dateparse.parse(date_limit_str) if date_limit_str else None
        count = 0
        num_failures = 0
        cursor = None

        while num_failures < BlueSky.FAILURE_LIMIT:
            try:
                rsp = self.client.app.bsky.notification.list_notifications(
                        params={'cursor': cursor})
                for notif in rsp.notifications:
                    if date_limit:
                        dt = datetime.strptime(notif.record.created_at,
                                               dateparse.BLUESKY_DATE_FORMAT)
                        if dt < date_limit:
                            # Once we get to notifications older than the date
                            # limit, we assume the rest of the notifications are
                            # older, we're done
                            self.logger.info('Date limit reached')
                            return

                    if count_limit:
                        count += 1
                        if count > count_limit:
                            self.logger.info('Count limit reached')
                            return

                    if notif.reason == 'reply':
                        post = self.get_post(notif.record.reply.parent.uri)
                    elif notif.reason in ['like', 'repost']:
                        post = self.get_post(notif.reason_subject)
                    else:
                        post = None

                    yield notif, post

                if rsp.cursor:
                    self.logger.info('Cursor found, retrieving next page...')
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            self.logger.error("Giving up, more than %s failures", self.FAILURE_LIMIT)

        if mark_read:
            seen_at = self.client.get_current_time_iso()
            self.client.app.bsky.notification.update_seen({'seen_at': seen_at})

    def search(self, term, author, date_limit_str, sort_order, is_follow, is_follower):
        '''A generator to yield posts that match the given search terms'''
        params = {'q': term,
                  'limit': 100,
                  'sort': sort_order}
        date_limit = dateparse.parse(date_limit_str) if date_limit_str else None
        if author:
            params['author'] = author
        if date_limit:
            params['since'] = date_limit.strftime('%Y-%m-%dT%H:%M:%SZ')

        if is_follow is None:
            follows = []
        else:
            follows = [entry.handle for entry in self.follows(self.handle)]
        if is_follower is None:
            followers = []
        else:
            followers = [entry.handle for entry in self.followers(self.handle)]

        cursor = None
        num_failures = 0

        while num_failures < self.FAILURE_LIMIT:
            params['cursor'] = cursor
            try:
                rsp = self.client.app.bsky.feed.search_posts(params=params)
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
                    self.logger.info('Cursor found, retrieving next page...')
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            self.logger.error("Giving up, more than %s failures", self.FAILURE_LIMIT)

    @normalize_handle
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

    @normalize_handle
    def follows(self, handle):
        '''A generator to return an entry for each user that the given user
           handle follows'''
        cursor = None
        num_failures = 0

        while num_failures < BlueSky.FAILURE_LIMIT:
            try:
                rsp = self.client.get_follows(handle, cursor=cursor)
                yield from rsp.follows
                if rsp.cursor:
                    self.logger.info('Cursor found, retrieving next page...')
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            self.logger.error("Giving up, more than %s failures", self.FAILURE_LIMIT)

    @normalize_handle
    def followers(self, handle):
        '''A generator to return an entry for each user that follows the given user
           handle'''
        cursor = None
        num_failures = 0

        while num_failures < BlueSky.FAILURE_LIMIT:
            try:
                rsp = self.client.get_followers(handle, cursor=cursor)
                yield from rsp.followers
                if rsp.cursor:
                    self.logger.info('Cursor found, retrieving next page...')
                    cursor = rsp.cursor
                else:
                    break
            except atproto_core.exceptions.AtProtocolError as ex:
                num_failures += 1
                self._print_at_protocol_error(ex)
        else:
            self.logger.error("Giving up, more than %s failures", self.FAILURE_LIMIT)

    def _login(self):
        self.client.login(self.handle, self._password)

    def _print_at_protocol_error(self, ex):
        self.logger.error(type(ex))
        if 'response' in dir(ex):
            if 'status_code' in dir(ex.response):
                self.logger.error("Status: %s", str(ex.response.status_code))
            if 'content' in dir(ex.response):
                if 'message' in dir(ex.response.content):
                    self.logger.error("Message: %s", ex.response.content.message)

    def normalize_handle_value(self, handle):
        '''Normalize the handle value. This assumes its wrapping a method from the
        BlueSky class'''
        hand = handle or self.handle
        if hand.startswith('did'):
            return hand
        if hand.startswith(self.PROFILE_URL):
            hand = hand.split('/')[-1]
        elif '.' not in hand:
            hand = hand + '.bsky.social'

        return hand.lstrip('@')

    def _get_image_data(self, filename):
        '''Read the image at the given filename and downsize it to under the
           max size permissible for blue sky'''
        scaler = 0.75
        count = 0

        self.logger.info("Reading image file %s", filename)
        with Image(filename=filename) as img:
            while count < 100:  # need some limit, surely 100 is enough
                img_data = img.make_blob()
                siz = len(img_data)
                self.logger.info("Image size is %d", siz)
                if siz < BlueSky.BLUESKY_MAX_IMAGE_SIZE:
                    break

                width = int(img.width * scaler)
                height = int(img.height * scaler)
                self.logger.info("Resizing image file to %dx%d", width, height)
                img.resize(width, height)
                count += 1

        return img_data
