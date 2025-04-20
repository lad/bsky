'''BlueSky tests'''

from unittest import mock
from unittest.mock import patch, MagicMock
import datetime

import atproto_core
import atproto_core.exceptions
import pytest
from base_test import BaseTest
from partial_failure import PartialFailure


# pylint: disable=W0613 (unused-argument)
# pylint: disable=W0201 (attribute-defined-outside-init)
# pylint: disable=R0903 (too-few-public-methods)


class MockHelpers:
    '''Helper functions for pytest mocks and fixtures'''
    @staticmethod
    def make_created_at(**kwargs):
        '''Create a timespec for reuse'''
        if kwargs:
            delta = datetime.timedelta(**kwargs)
        else:
            delta = datetime.timedelta()
        now = datetime.datetime.now(datetime.UTC) - delta
        return now.isoformat(timespec='milliseconds')

# rsp = self.client.app.bsky.notification.list_notifications(
# for notif in rsp.notifications:
# if date_limit:
#   dt = datetime.strptime(notif.record.created_at,
# if count_limit:
# if notif.reason == 'reply':
#     post = self.get_post(notif.record.reply.parent.uri)
# elif notif.reason in ['like', 'repost']:
#     post = self.get_post(notif.reason_subject)
# else:
#     post = None
# cursor = rsp.cursor
# elif mark_read:
#     seen_at = self.client.get_current_time_iso()
#     self.client.app.bsky.notification.update_seen({'seen_at': seen_at})
# except atproto_core.exceptions.AtProtocolError as ex:


class TestGetNotifications(BaseTest):
    '''Test BlueSky get_notifications() method'''
    @staticmethod
    def mock_post_uri(num):
        '''Create a mock URI for post resources'''
        return f"at://example/post/{num}"

    @staticmethod
    def mock_notification_reply(num):
        '''Create a mock notification structure for replies'''
        notif = MagicMock()
        notif.record.created_at = MockHelpers.make_created_at()
        notif.reason = 'reply'
        notif.record.reply.parent.uri = TestGetNotifications.mock_post_uri(num)
        notif.is_read = False
        notif.cursor = None
        return notif

    @staticmethod
    def mock_notification_like(num):
        '''Create a mock notification structure for likes'''
        notif = MagicMock()
        notif.record.created_at = MockHelpers.make_created_at()
        notif.reason = 'like'
        notif.reason_subject = TestGetNotifications.mock_post_uri(num)
        notif.is_read = False
        notif.cursor = None
        return notif

    @pytest.fixture
    def mock_40_not_read_notifications(self):
        '''Create 40 mock notification structures of various types'''
        rsp = MagicMock()

        # Build a list and intersperse the reply and like notifications
        reply = self.mock_notification_reply
        like = self.mock_notification_like

        rsp.notifications = [reply(i) for i in range(1, 11)] + \
                            [like(i) for i in range(11, 21)] + \
                            [reply(i) for i in range(21, 41)]
        rsp.cursor = None
        return rsp

    @staticmethod
    def side_effect_post(uri):
        '''Create a mock post structure with the given URI'''
        post = MagicMock()
        post.uri = uri
        return post

    def test_get_notifications_no_date_no_count_no_mark_read(
            self, mock_40_not_read_notifications):
        '''Test notifications with no date limit, no count limit and not marking
           any as read'''
        with patch.object(self.instance, 'get_post',
                          side_effect=TestGetNotifications.side_effect_post), \
             patch.object(self.instance.client.app.bsky.notification,
                          'list_notifications',
                          return_value=mock_40_not_read_notifications):
            responses = list(self.instance.get_notifications())

            assert len(responses) == 40
            for i, (notification, post) in enumerate(responses):
                assert notification.created_at is not None
                assert post.uri == TestGetNotifications.mock_post_uri(i + 1)

    def test_get_notifications_no_date_with_count_with_mark_read(
            self, mock_40_not_read_notifications):
        '''Test notifications with marking notification as read. Count needed to
           have get_notification return early. Test ensures notifications are
           marked as read even in that case.'''
        with patch.object(self.instance, 'get_post',
                          side_effect=TestGetNotifications.side_effect_post), \
             patch.object(self.instance.client.app.bsky.notification,
                          'list_notifications',
                          return_value=mock_40_not_read_notifications), \
             patch.object(self.instance.client.app.bsky.notification,
                          'update_seen') as update_seen:

            responses = list(self.instance.get_notifications(count_limit=5,
                                                             mark_read=True))
            assert len(responses) == 5
            assert update_seen.call_count == 1

    def test_get_notifications_no_date_no_count_no_mark_read_with_cursor(
            self, mock_40_not_read_notifications):
        '''Test notifications with no date limit, no count limit and not marking
           any as read but returning in several "pages" with a cursor'''

        def side_effect_list_notifications_cursor(params=None):
            cursor = params['cursor']
            rsp = MagicMock()
            if cursor is None:
                rsp.notifications = mock_40_not_read_notifications.notifications[0:10]
                rsp.cursor = 10
            elif cursor == 10:
                rsp.notifications = mock_40_not_read_notifications.notifications[10:19]
                rsp.cursor = 20
            elif cursor == 20:
                rsp.notifications = mock_40_not_read_notifications.notifications[19:29]
                rsp.cursor = 30
            elif cursor == 30:
                rsp.notifications = mock_40_not_read_notifications.notifications[29:37]
                rsp.cursor = 38
            elif cursor == 38:
                rsp.notifications = mock_40_not_read_notifications.notifications[37:40]
                rsp.cursor = None
            return rsp

        post = MagicMock()
        with patch.object(self.instance, 'get_post',
                          side_effect=TestGetNotifications.side_effect_post), \
             patch.object(self.instance.client.app.bsky.notification,
                          'list_notifications',
                          side_effect=side_effect_list_notifications_cursor):
            responses = list(self.instance.get_notifications())
            assert len(responses) == 40
            for i, (notification, post) in enumerate(responses):
                assert notification.created_at is not None
                assert post.uri == TestGetNotifications.mock_post_uri(i + 1)

    def test_get_notifications_exception_limit(self):
        '''Test BlueSky.get_notifications() when
           .client.app.bsky.notification.list_notifications raises exceptions'''
        with patch.object(self.instance.client.app.bsky.notification,
                          'list_notifications',
                          side_effect=atproto_core.exceptions.AtProtocolError(
                              'Mocked Exception')) as mock_ln:
            with pytest.raises(IOError):
                list(self.instance.get_notifications())
            assert mock_ln.call_count == self.instance.FAILURE_LIMIT

    @pytest.mark.parametrize("ex", [AssertionError, KeyError, NameError, ValueError])
    def test_get_notifications_non_atproto_exceptions(self, ex):
        '''Test BlueSky.get_notifications() when get_actor_likes raises non atproto
           exceptions'''
        with patch.object(self.instance.client.app.bsky.notification,
                          'list_notifications',
                          side_effect=ex('Mocked Exception')):
            # get_notifications() is a generator, use list() to ensure it is
            # actually invoked
            with pytest.raises(ex):
                list(self.instance.get_notifications(None))

    def test_get_notifications_date_parse_exception(self):
        '''Test when an invalid date is provided'''
        with pytest.raises(ValueError):
            list(self.instance.get_notifications("invalid-date"))

    def side_effect_feed_like_get(self, _did, rkey):
        '''Create a mock response for bsky.app.feed.like.get()'''
        like_get_mock = MagicMock()
        like_get_mock.value = MagicMock()
        # Use the rkey part of the URI as the number of minutes old that the
        # like was created at. We setup these rkey/URI values as an increasing
        # integer from 1 in setup_10_gal_mock()
        like_get_mock.value.created_at = MockHelpers.make_created_at(minutes=int(rkey))
        self.like_get_mock_feed_created_at.append(like_get_mock.value.created_at)
        return like_get_mock

    @pytest.mark.parametrize("minutes_ago", range(11))
    @pytest.mark.skip
    def test_get_notifications_date_limit_reached_no_count(self, setup_10_gal_mock,
                                                           minutes_ago):
        '''Test when the date limit is reached'''
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes', return_value=setup_10_gal_mock), \
            patch.object(self.instance.client.app.bsky.feed.like,
                         'get', side_effect=self.side_effect_feed_like_get):

            # The side effect function self.mock_feed_like_get() saves the created_at
            # dates in this list. We can assert that we get back these created_at
            # dates in the likes returned from get_likes()
            self.like_get_mock_feed_created_at = []

            # Call function under test: get_likes() with a date limit but no count
            # and get_date=False.
            #
            # This test is parameterized with the date limit string. It corresponds to
            # the number of likes we will get back from get_likes(). The likes have
            # been setup by setup_10_gal_mock() with created_at fields decreasing by
            # <param> minutes ago. So a date limit string of "1 minute ago"
            # should give 1 like, "10 minutes ago" should give 10 likes
            likes = list(self.instance.get_likes(f"{minutes_ago} minutes ago"))

            # assert the number of likes returned
            assert len(likes) == minutes_ago

            # assert the contents of the returned likes
            for like, mock_feed, created_at in zip(likes, setup_10_gal_mock.feed,
                                                   self.like_get_mock_feed_created_at):
                assert like.post.viewer.like == mock_feed.post.viewer.like
                assert like.post.uri == mock_feed.post.uri
                assert like.created_at is not None
                assert like.created_at == created_at

    @pytest.mark.parametrize("count_limit", range(1, 11))
    def test_get_notifications_no_date_count_limit_reached(
            self, mock_40_not_read_notifications, count_limit):
        '''Test when the date limit is reached'''
        with patch.object(self.instance, 'get_post',
                          side_effect=TestGetNotifications.side_effect_post), \
             patch.object(self.instance.client.app.bsky.notification,
                          'list_notifications',
                          return_value=mock_40_not_read_notifications):

            # Call function under test: get_notifications() with a date limit
            # but no count and get_date=False.
            #
            # This test is parameterized with a count limit. This is the total number
            # of likes that we should get back from get_likes(). No date limit string
            # is provided so the created_at dates of the likes should be ignored
            responses = list(self.instance.get_notifications(None, count_limit))

            # assert the number of likes returned
            assert len(responses) == count_limit

            # assert the contents of the returned likes
            for i, (notification, post) in enumerate(responses):
                assert post.uri == TestGetNotifications.mock_post_uri(i + 1)
                assert notification.created_at is not None

    def test_get_notifications_with_empty_feed(self):
        '''Test when the feed is empty'''
        self.instance.client.app.bsky.feed.get_actor_likes.return_value = \
            mock.Mock(feed=[], cursor=None)
        rsp = MagicMock()
        rsp.notifications = []
        rsp.cursor = None

        with patch.object(self.instance.client.app.bsky.notification,
                          'list_notifications', return_value=rsp):
            responses = list(self.instance.get_notifications())
            assert not responses
