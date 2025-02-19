'''BlueSky class to interact with the Blue Sky API via atproto'''

import os
from datetime import datetime
import tzlocal

import atproto
import atproto_core
import wcwidth
from wand.image import Image

import informal_date

CONFIG_PATH_DEFAULT = os.path.join(os.getcwd(), '.config')
BLUESKY_MAX_IMAGE_SIZE = 976.56 * 1024
DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
LOCAL_TIMEZONE = tzlocal.get_localzone()


class BlueSky:
    '''Command line client for Blue Sky'''
    def __init__(self, handle, password):
        self._handle = handle
        self._password = password
        self._client = atproto.Client()
        self._login()

    def likes(self, date_limit_str, show_date):
        '''Output the posts that the given user handle has liked'''
        params = {
                "actor": self._handle,
                #"limit": 100,  # Optional: specify the number of likes to retrieve
                }
        cursor = None

        if date_limit_str:
            date_limit = informal_date.parse(date_limit_str).replace(
                                                        tzinfo=LOCAL_TIMEZONE)
        else:
            date_limit = None

        while True:
            params['cursor'] = cursor
            rsp = self._client.app.bsky.feed.get_actor_likes(params=params)
            if not rsp.feed:
                break

            for like in rsp.feed:
                did, rkey = self._at_uri_to_did_rkey(like.post.viewer.like)
                if date_limit or show_date:
                    like_rsp = self._client.app.bsky.feed.like.get(did, rkey)
                    created_at = like_rsp.value.created_at
                    like_date = BlueSky._humanise_date_string(created_at)
                else:
                    like_date = None

                if date_limit:
                    dt = datetime.strptime(created_at, DATE_FORMAT)
                    if dt < date_limit:
                        return

                handle = like.post.author.handle
                author_profile = self._client.get_profile(handle)
                followers = author_profile.followers_count
                print(f"Author: {handle} "
                      f"{like.post.author.display_name} ({followers} followers)\n"
                      f"Author Link: https://bsky.app/profile/{handle}\n"
                      f"Post Link: {self._at_uri_to_http_url(like.post.uri)}\n"
                      f"Text: {like.post.record.text}")
                if like_date:
                    print(f"Like Date: {like_date}")
                print('-----')

            if rsp.cursor:
                cursor=rsp.cursor
            else:
                break

    def follows(self, handle, full):
        '''Output a list of users and their DIDs that the given user handle follows'''
        for entry in self._get_follows(handle):
            self._print_user_entry(entry, full)

    def followers(self, handle, full):
        '''Output a list of users and their DIDs that follow the given user handle'''
        for entry in self._get_followers(handle):
            self._print_user_entry(entry, full)

    def mutuals(self, handle, flag):
        '''Output a list of users that the given user follows and who are also
           followers of the given user, if flag == both.
           If flag == follows-not-followers output list of users that the user
           follows who don't follow back.
           If flag = followers-not-follows  output list of users that follow
           this user that this user does not follow back'''

        follows = set(entry.handle for entry in self._get_follows(handle))
        followers = set(entry.handle for entry in self._get_followers(handle))

        if flag == 'both':
            result = follows & followers
        elif flag == 'follows-not-followers':
            result = follows - followers
        elif flag == 'followers-not-follows':
            result = followers - follows
        else:
            raise ValueError(f"Invalid flag: '{flag}'. Expected 'both', "
                              "'follows-not-followers', or 'followers-not-follows'.")

        for entry in result:
            print(entry)

    def posts(self, handle=None, date_limit_str=None, count=None):
        '''Output all posts for the given user handle'''
        if date_limit_str:
            date_limit = informal_date.parse(date_limit_str).replace(
                                                        tzinfo=LOCAL_TIMEZONE)
        else:
            date_limit = None

        for post in self._get_posts(handle, date_limit=date_limit, count_limit=count):
            self._print_post_entry(post)

    def reposters(self, handle, full):
        '''Output a list of all people that have reposts posts for the given user
           handle'''
        repost_info = {}

        for post in self._get_posts(handle):
            if post.repost_count:
                reposters = self._client.get_reposted_by(post.uri)
                for r in reposters.reposted_by:
                    if r.handle in repost_info:
                        repost_info[r.handle]['count'] += 1
                    else:
                        repost_info[r.handle] = {
                                'count': 1,
                                'display_name': r.display_name
                        }

        sorted_items = sorted(repost_info.items(),
                              key=lambda item: item[1]['count'], reverse=True)

        count = 0
        for hand, info in sorted_items:
            if full:
                print(f"@{hand} ({info['display_name']}): {info['count']} reposts")
                count += info['count']
            else:
                print(f"@{hand}")
        if full:
            print(f"{count} reposts in total")

    def post(self, text, show_uri):
        '''Post the given text'''
        post = self._client.send_post(text)
        if show_uri:
            print(post.uri)

    def post_image(self, text, filename, alt):
        '''Post the given image with the given text and given alt-text'''
        img_data = self._get_image_data(filename)

        # Add image aspect ratio to prevent default 1:1 aspect ratio
        # Replace with your desired aspect ratio
        aspect_ratio = atproto.models.AppBskyEmbedDefs.AspectRatio(
                            height=100, width=100)

        print('Sending')
        rsp = self._client.send_image(text=text,
                                      image=img_data,
                                      image_alt=alt or '',
                                      image_aspect_ratio=aspect_ratio)
        print(rsp.uri)

    def delete(self, uri):
        '''delete the post at the given uri'''
        rsp = self._client.delete_post(uri)
        print(rsp)

    def profile(self, handle):
        '''output the profile of the given user handle'''
        profile = self._client.get_profile(handle or self._handle)
        self._print_user_entry(profile, True)

    def notifications(self, date_limit_str=None, showall=False, mark_read=False):
        '''output the unacknowledged notifications for the authenticated handle'''
        if date_limit_str:
            date_limit = informal_date.parse(date_limit_str).replace(
                                                        tzinfo=LOCAL_TIMEZONE)
        else:
            date_limit = None

        rsp = self._client.app.bsky.notification.list_notifications()
        notification_count, unread_count = 0, 0

        for notif in rsp.notifications:
            if date_limit:
                dt = datetime.strptime(notif.record.created_at, DATE_FORMAT)
                if dt < date_limit:
                    continue

            if showall or not notif.is_read:
                print(f"From: {notif.author.handle}")
                print(f"Reason: {notif.reason}")
                print(f"Date: {self._humanise_date_string(notif.indexed_at)}")
                if notif.reason == 'reply':
                    print(f"Text: {notif.record.text}")
                    did, rkey = self._at_uri_to_did_rkey(
                                            notif.record.reply.parent.uri)
                    try:
                        post = self._client.get_post(rkey, profile_identify=did)
                        print(f"In reply to: {post.value.text}")
                    except atproto_core.exceptions.AtProtocolError as ex:
                        print(ex.response.status_code)
                        print(ex.response.content.message)
                elif notif.reason == 'like':
                    did, rkey = self._at_uri_to_did_rkey(notif.reason_subject)
                    try:
                        post = self._client.get_post(rkey, profile_identify=did)
                        print(f"Post: {post.value.text}")
                    except atproto_core.exceptions.AtProtocolError as ex:
                        print('Exception while retrieving liked post')
                        print(f"Status: {ex.response.status_code}")
                        print(f"Message: {ex.response.content.message}")
                print('--')
                if not notif.is_read:
                    unread_count += 1
            notification_count += 1
        print(f"{notification_count} notifications, "
              f"{notification_count - unread_count} read, "
              f"{unread_count} unread")

        if mark_read:
            seen_at = self._client.get_current_time_iso()
            self._client.app.bsky.notification.update_seen({'seen_at': seen_at})

    def profile_did(self, handle):
        '''Output the DID for a given user handle'''
        user_profile = self._client.get_profile(handle)
        print(user_profile.did)

    def _login(self):
        self._client.login(self._handle, self._password)

    @staticmethod
    def _ljust(text, length, padding=' '):
        return text + padding * max(0, (length - wcwidth.wcswidth(text)))

    @staticmethod
    def _at_uri_to_http_url(at_uri):
        '''return the http address of the given at-uri'''
        did, rkey = BlueSky._at_uri_to_did_rkey(at_uri)
        return f"https://bsky.app/profile/{did}/post/{rkey}"

    @staticmethod
    def _at_uri_to_did_rkey(at_uri):
        '''return the DID and rkey of the given at-uri'''
        _, _, did, _, rkey = at_uri.split('/')
        return did, rkey

    @staticmethod
    def _humanise_date_string(date_string):
        try:
            return datetime.strptime(date_string, DATE_FORMAT) \
                           .strftime('%B %d, %Y at %I:%M %p UTC')
        except ValueError:
            # Failed to parse string, return it as a simple string
            return str(date_string)

    def _get_follows(self, handle):
        '''A generator to return an entry for each user that the given user
           handle follows'''
        cursor = None
        while True:
            rsp = self._client.get_follows(handle or self._handle, cursor=cursor)
            yield from rsp.follows
            if rsp.cursor:
                cursor = rsp.cursor
            else:
                break

    def _get_followers(self, handle):
        '''A generator to return an entry for each user that follows the given user
           handle'''
        cursor = None
        while True:
            rsp = self._client.get_followers(handle or self._handle, cursor=cursor)
            yield from rsp.followers
            if rsp.cursor:
                cursor = rsp.cursor
            else:
                break

    @staticmethod
    def _print_user_entry(entry, full=False):
        if full:
            print("Display Name: ", entry.display_name, "\n",
                  "Handle:       ", entry.handle, "\n",
                  "DID:          ", entry.did, "\n",
                  "Created at:   ", BlueSky._humanise_date_string(entry.created_at),
                  sep='')
            if entry.description:
                print("Description:  ",
                    entry.description.replace("\n", "\n              "), "\n",
                    sep='')
        else:
            print(entry.handle)

    def _get_posts(self, handle=None, date_limit=None, count_limit=None):
        '''A generator to return an entry for posts for the given user handle'''
        cursor = None
        actor = handle or self._handle
        count = 0

        while True:
            feed = self._client.get_author_feed(actor=actor, cursor=cursor)
            for view in feed.feed:
                if date_limit:
                    dt = datetime.strptime(view.post.record.created_at, DATE_FORMAT)
                    if dt < date_limit:
                        return
                if count_limit:
                    count += 1
                    if count > count_limit:
                        return
                yield view.post

            if feed.cursor:
                cursor = feed.cursor
            else:
                break

    @staticmethod
    def _print_post_entry(post):
        txt = post.record.text
        print(txt)
        print(BlueSky._humanise_date_string(post.record.created_at))
        print(BlueSky._at_uri_to_http_url(post.uri))
        print(post.uri)
        print(post.like_count)
        print()

    @staticmethod
    def _get_image_data(filename):
        '''Read the image at the given filename and downsize it to under the
           max size permissible for blue sky'''
        scaler = 0.75

        print('Reading image')
        with Image(filename=filename) as img:
            while True:
                img_data = img.make_blob()
                if len(img_data) < BLUESKY_MAX_IMAGE_SIZE:
                    break

                print('Resizing', img.size)
                img.resize(int(img.width * scaler), int(img.height * scaler))

        return img_data
