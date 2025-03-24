'''BlueSky tests'''

from unittest import mock
from unittest.mock import patch, MagicMock
import datetime

import atproto_core
import atproto_core.exceptions

import pytest

from base_test import BaseTest
from bluesky import BlueSky


# pylint: disable=W0613 (unused-argument)
# pylint: disable=W0201 (attribute-defined-outside-init)


class MockHelpers:
    '''Helper functions for pytest mocks and fixtures'''
    @staticmethod
    def like_created_at(**kwargs):
        '''Create a timespec for reuse'''
        if kwargs:
            delta = datetime.timedelta(**kwargs)
        else:
            delta = datetime.timedelta()
        now = datetime.datetime.now(datetime.UTC) - delta
        return now.isoformat(timespec='milliseconds')

    @staticmethod
    def create_like_mock(num=1):
        '''Create like mock object. Used by several fixtures'''
        like_mock = MagicMock()
        like_mock.post = MagicMock()
        like_mock.post.viewer = MagicMock()
        like_mock.post.viewer.like = f"at://example/did/{num}"
        like_mock.post.uri = f"at://example/post/{num}"
        # Do not set .created_at. This should be set when get_likes() calls
        # client.bsky.feed.like.get()
        return like_mock

    @staticmethod
    def create_gal_mocks(num):
        '''Create a mock response for get_actor_likes(). Used by several fixtures'''
        gal_mock = MagicMock()
        gal_mock.feed = [MockHelpers.create_like_mock(i+1) for i in range(num)]
        gal_mock.cursor = None
        return gal_mock


class TestGetLikes(BaseTest):
    '''Test BlueSky get_likes() method'''
    @pytest.fixture
    def setup_like_mock(self):
        '''Create a mock like object with a valid structure'''
        return MockHelpers.create_like_mock()

    @pytest.fixture(params=[0, 1, 2, 3])
    def setup_gal_mock(self, request, setup_like_mock):
        '''Create a mock response for get_actor_likes()'''
        return MockHelpers.create_gal_mocks(request.param), request.param

    @pytest.fixture
    def setup_10_gal_mock(self):
        '''Create a mock response for get_actor_likes()'''
        return MockHelpers.create_gal_mocks(10)

    @pytest.fixture
    def setup_like_get_mock(self):
        '''Create a mock response for like.get()'''
        like_get_mock = MagicMock()
        like_get_mock.value = MagicMock()
        like_get_mock.value.created_at = MockHelpers.like_created_at()
        return like_get_mock

    def test_get_likes_gal_exception_limit(self):
        '''Test BlueSky.get_likes() when get_actor_likes() raises exceptions'''
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes',
                          side_effect=atproto_core.exceptions.AtProtocolError(
                                                'Mocked Exception')) as gal_mock:
            # get_likes() is a generator, use list() to ensure it is actually invoked
            assert not list(self.instance.get_likes(None))
            assert gal_mock.call_count == BlueSky.FAILURE_LIMIT

    def test_get_likes_get_exception_limit(self, setup_10_gal_mock):
        '''Test BlueSky.get_likes() when app.bsky.feed.like.get() raises exceptions'''
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes', return_value=setup_10_gal_mock), \
             patch.object(self.instance.client.app.bsky.feed.like,
                          'get',
                          side_effect=atproto_core.exceptions.AtProtocolError(
                                                'Mocked Exception')) as get_mock:
            # get_likes() is a generator, use list() to ensure it is actually invoked
            assert not list(self.instance.get_likes(None, get_date=True))
            assert get_mock.call_count == BlueSky.FAILURE_LIMIT

    @pytest.mark.parametrize("ex", [AssertionError, KeyError, NameError, ValueError])
    def test_get_likes_non_atproto_exceptions(self, ex):
        '''Test BlueSky.get_likes() when get_actor_likes raises non atproto
           exceptions'''
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes',
                          side_effect=ex('Mocked Exception')):
            # get_likes() is a generator, use list() to ensure it is actually invoked
            with pytest.raises(ex):
                list(self.instance.get_likes(None))

    @pytest.mark.parametrize("ex", [AssertionError, KeyError, NameError, ValueError])
    def test_get_likes_non_atproto_exceptions2(self, setup_10_gal_mock, ex):
        '''Test BlueSky.get_likes() when get_actor_likes raises non atproto
           exceptions'''
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes', return_value=setup_10_gal_mock), \
             patch.object(self.instance.client.app.bsky.feed.like,
                          'get',
                          side_effect=ex('Mocked Exception')):
            # get_likes() is a generator, use list() to ensure it is actually invoked
            with pytest.raises(ex):
                list(self.instance.get_likes(None, get_date=True))

    def test_get_likes_date_parse_exception(self):
        '''Test when an invalid date is provided'''
        with pytest.raises(ValueError):
            list(self.instance.get_likes("invalid-date"))

    def test_get_likes_no_date_no_count_no_get_date(self, setup_gal_mock):
        '''Test the get_likes method, no date, no count, get_date default (false)'''
        gal_mock, param = setup_gal_mock
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes', return_value=gal_mock):

            # Call function under test: get_likes() with no date and no count
            likes = list(self.instance.get_likes(None))

            # assert the number of likes returned
            assert len(likes) == param

            # assert the contents of the returned likes
            for like, mock_feed in zip(likes, gal_mock.feed):
                assert like.post.viewer.like == mock_feed.post.viewer.like
                assert like.post.uri == mock_feed.post.uri
                # no date limit string was provided and get_date is False so we
                # should not get back a valid created_at field.
                assert like.created_at is None

    def test_get_likes_no_date_no_count_get_date(self,
                                                 setup_gal_mock, setup_like_get_mock):
        '''Test the get_likes method, no date, no count, get_date True'''
        gal_mock, param = setup_gal_mock
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes', return_value=gal_mock), \
            patch.object(self.instance.client.app.bsky.feed.like,
                         'get', return_value=setup_like_get_mock):

            # Call function under test: get_likes() with no date and no count and
            # get_date=True
            likes = list(self.instance.get_likes(None, get_date=True))

            # assert the number of likes returned
            assert len(likes) == param

            # assert the contents of the returned likes
            for like, mock_feed in zip(likes, gal_mock.feed):
                assert like.post.viewer.like == mock_feed.post.viewer.like
                assert like.post.uri == mock_feed.post.uri
                # get_date was True so we should get back a valid date
                assert like.created_at is not None
                assert like.created_at == mock_feed.created_at

    def test_get_likes_no_date_no_count_get_date_with_retries(
            self, setup_gal_mock, setup_like_get_mock):
        '''Test the get_likes method, no date, no count, get_date True when
           some exceptions occur focing retries'''
        gal_mock, param = setup_gal_mock
        num_exceptions = 2

        # Throw exceptions twice from the get_actor_likes mock. This should force
        # retries in get_likes(). On the third try it will return the mock object.
        def side_effect_atproto_exceptions(params=None):
            nonlocal num_exceptions
            num_exceptions -= 1
            if num_exceptions >= 0:
                raise atproto_core.exceptions.AtProtocolError('Mocked Exception')
            return gal_mock

        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes',
                          side_effect=side_effect_atproto_exceptions), \
            patch.object(self.instance.client.app.bsky.feed.like,
                         'get', return_value=setup_like_get_mock):

            # Call function under test: get_likes() with no date and no count and
            # get_date=True
            likes = list(self.instance.get_likes(None, get_date=True))

            # assert the number of likes returned
            assert len(likes) == param

            # assert the contents of the returned likes
            for like, mock_feed in zip(likes, gal_mock.feed):
                assert like.post.viewer.like == mock_feed.post.viewer.like
                assert like.post.uri == mock_feed.post.uri
                # get_date was True so we should get back a valid date
                assert like.created_at is not None
                assert like.created_at == mock_feed.created_at

    def side_effect_feed_like_get(self, did, rkey):
        '''Create a mock response for bsky.app.feed.like.get()'''
        like_get_mock = MagicMock()
        like_get_mock.value = MagicMock()
        # Use the rkey part of the URI as the number of minutes old that the
        # like was created at. We setup these rkey/URI values as an increasing
        # integer from 1 in setup_10_gal_mock()
        like_get_mock.value.created_at = MockHelpers.like_created_at(minutes=int(rkey))
        self.like_get_mock_feed_created_at.append(like_get_mock.value.created_at)
        return like_get_mock

    @pytest.mark.parametrize("minutes_ago", range(11))
    def test_get_likes_date_limit_reached_no_count(self, setup_10_gal_mock,
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
    def test_get_likes_no_date_count_limit_reached(self, setup_10_gal_mock,
                                                   count_limit):
        '''Test when the date limit is reached'''
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes', return_value=setup_10_gal_mock):

            # Call function under test: get_likes() with a date limit but no count
            # and get_date=False.
            #
            # This test is parameterized with a count limit. This is the total number
            # of likes that we should get back from get_likes(). No date limit string
            # is provided so the created_at dates of the likes should be ignored
            likes = list(self.instance.get_likes(None, count_limit))

            # assert the number of likes returned
            assert len(likes) == count_limit

            # assert the contents of the returned likes
            for like, mock_feed, in zip(likes, setup_10_gal_mock.feed):

                assert like.post.viewer.like == mock_feed.post.viewer.like
                assert like.post.uri == mock_feed.post.uri
                assert like.created_at is None

    def test_get_likes_with_cursor(self, setup_like_get_mock):
        '''Test when there are multiple pages of likes'''

        gal_mocks_feed = []

        # Return 6 likes in total in three "pages", i.e. three different cursor
        # values returned and expect that we get the cursor back again for the
        # next page of likes. We also save the .feed list from each mock returned
        # and use it to test against the likes returned from get_likes()
        def side_effect_gal_cursor(params=None):
            nonlocal gal_mocks_feed

            cursor = params['cursor']
            if cursor is None:
                gal_mock = MockHelpers.create_gal_mocks(3)
                gal_mock.cursor = 3
            elif cursor == 3:
                gal_mock = MockHelpers.create_gal_mocks(2)
                gal_mock.cursor = 5
            elif cursor == 5:
                gal_mock = MockHelpers.create_gal_mocks(1)
                gal_mock.cursor = 6
            elif cursor == 6:
                gal_mock = MockHelpers.create_gal_mocks(2)
                gal_mock.cursor = None
            gal_mocks_feed.extend(gal_mock.feed)
            return gal_mock

        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes',
                          side_effect=side_effect_gal_cursor), \
            patch.object(self.instance.client.app.bsky.feed.like,
                         'get', return_value=setup_like_get_mock):

            # Call function under test: get_likes() with no date and no count and
            # get_date=True
            likes = list(self.instance.get_likes(None, get_date=True))

            # assert the number of likes returned
            assert len(likes) == 8

            # assert the contents of the returned likes against the mocks supplied
            # to get_likes()
            for like, mock_feed in zip(likes, gal_mocks_feed):
                assert like.post.viewer.like == mock_feed.post.viewer.like
                assert like.post.uri == mock_feed.post.uri
                # get_date was True so we should get back a valid date
                assert like.created_at is not None
                assert like.created_at == mock_feed.created_at

    def test_get_likes_with_empty_feed(self):
        '''Test when the feed is empty'''
        self.instance.client.app.bsky.feed.get_actor_likes.return_value = \
            mock.Mock(feed=[], cursor=None)

        result = list(self.instance.get_likes("2023-01-01"))
        assert not result
