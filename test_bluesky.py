'''BlueSky tests'''

from unittest import mock
from unittest.mock import patch, MagicMock
import datetime
import copy

import atproto_core
import atproto_core.exceptions

import pytest
from bluesky import BlueSky

# pylint: disable=W0613 (unused-argument)
# pylint: disable=R0904 (too-many-public-methods)
# pylint: disable=W0201 (attribute-defined-outside-init)


class TestGetLikes:
    '''Test BlueSky get_likes() method'''
    @pytest.fixture
    def setup_method(self):
        '''Create an instance of the class containing the get_likes method'''
        with patch('atproto.Client') as mock_client:
            mock_client_instance = mock_client.return_value
            mock_client_instance.login.return_value = None  # Mock the login method
            self.instance = BlueSky(handle='@testuser.bsky.social',
                                    password='testpassword')

    def like_created_at(self, **kwargs):
        '''Create a timespec for reuse'''
        if kwargs:
            delta = datetime.timedelta(**kwargs)
        else:
            delta = datetime.timedelta()
        now = datetime.datetime.now(datetime.UTC) - delta
        return now.isoformat(timespec='milliseconds')

    @pytest.fixture
    def setup_like_mock(self):
        '''Create a mock like object with a valid structure'''
        like_mock = MagicMock()
        like_mock.post = MagicMock()
        like_mock.post.viewer = MagicMock()
        like_mock.post.viewer.like = 'at://example/did/1'
        like_mock.post.uri = 'at://example/post/1'
        # Do not set .created_at. This should be set when get_likes() calls
        # client.bsky.feed.like.get()
        return like_mock

    @pytest.fixture(params=[0, 1, 2, 3])
    def setup_gal_mock(self, request, setup_like_mock):
        '''Create a mock response for get_actor_likes()'''
        gal_mock = MagicMock()
        gal_mock.feed = []
        # Number of like mocks depends on test fixture param
        for i in range(request.param):
            like_mock_copy = copy.deepcopy(setup_like_mock)
            like_mock_copy.post.uri = f"at://example/post/{i}"
            gal_mock.feed.append(like_mock_copy)
        gal_mock.cursor = None
        return gal_mock, request.param

    @pytest.fixture
    def setup_10_like_mocks(self):
        '''Create 10  mocks like object with a valid structure'''
        like_mocks = []
        for i in range(10):
            like_mock = MagicMock()
            like_mock.post = MagicMock()
            like_mock.post.viewer = MagicMock()
            like_mock.post.viewer.like = f"at://example/did/{i+1}"
            like_mock.post.uri = f"at://example/post/{i+1}"
            # Do not set .created_at. This should be set when get_likes() calls
            # client.bsky.feed.like.get()
            like_mocks.append(like_mock)
        return like_mocks

    @pytest.fixture
    def setup_10_gal_mock(self, setup_10_like_mocks):
        '''Create a mock response for get_actor_likes()'''
        gal_mock = MagicMock()
        gal_mock.feed = setup_10_like_mocks
        gal_mock.cursor = None
        return gal_mock

    @pytest.fixture
    def setup_like_get_mock(self):
        '''Create a mock response for like.get()'''
        like_get_mock = MagicMock()
        like_get_mock.value = MagicMock()
        like_get_mock.value.created_at = self.like_created_at()
        return like_get_mock

    def test_get_likes_failures(self, setup_method):
        '''Test BlueSky.get_likes() when get_actor_likes() raises exceptions'''
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes',
                          side_effect=atproto_core.exceptions.AtProtocolError(
                                                'Mocked Exception')) as gal_mock:
            # get_likes() is a generator, use list() to ensure it is actually invoked
            assert not list(self.instance.get_likes(None))
            assert gal_mock.call_count == BlueSky.FAILURE_LIMIT

    def test_get_likes_no_date_no_count_no_get_date(self,
                                                    setup_method,
                                                    setup_gal_mock,
                                                    setup_like_get_mock):
        '''Test the get_likes method, no date, no count, get_date default (false)'''
        # Mock the API call to return the mock response
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

    def test_get_likes_no_date_no_count_get_date(self, setup_method,
                                                 setup_gal_mock, setup_like_get_mock):
        '''Test the get_likes method, no date, no count, get_date True'''
        # Mock the API call to return the mock response
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

    def mock_feed_like_get(self, did, rkey):
        '''Create a mock response for bsky.app.feed.like.get()'''
        like_get_mock = MagicMock()
        like_get_mock.value = MagicMock()
        # Use the rkey part of the URI as the number of minutes old that the
        # like was created at. We setup these rkey/URI values as an increasing
        # integer from 1 in setup_10_like_mocks()
        like_get_mock.value.created_at = self.like_created_at(minutes=int(rkey))
        self.like_get_mock_feed_created_at.append(like_get_mock.value.created_at)
        return like_get_mock

    @pytest.mark.parametrize("minutes_ago", range(10))
    def test_get_likes_date_limit_reached(self, setup_method, setup_10_gal_mock,
                                          minutes_ago):
        '''Test when the date limit is reached'''
        # Mock the API call to return the mock response
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes', return_value=setup_10_gal_mock), \
            patch.object(self.instance.client.app.bsky.feed.like,
                         'get', side_effect=self.mock_feed_like_get):

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
            # <n> minutes ago. So a date limit string of "1 minute ago" should give 1
            # like up to "10 minutes ago" should give 10 likes
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

    @pytest.mark.skip
    def test_get_likes_count_limit_reached(self, setup_method):
        '''Test when the count limit is reached'''
        like_mock = mock.Mock()
        like_mock.viewer.like = ("did", "rkey")
        like_mock.created_at = "2023-01-01T00:00:00Z"

        self.instance.client.app.bsky.feed.get_actor_likes.return_value = \
            mock.Mock(feed=[like_mock, like_mock], cursor=None)
        self.instance.client.app.bsky.feed.like.get.return_value = \
            mock.Mock(value=like_mock)

        result = list(self.instance.get_likes("2023-01-01", count_limit=1))
        assert len(result) == 1

    @pytest.mark.skip
    def test_get_likes_with_cursor(self, setup_method):
        '''Test when there are multiple pages of likes'''
        like_mock = mock.Mock()
        like_mock.viewer.like = ("did", "rkey")
        like_mock.created_at = "2023-01-01T00:00:00Z"

        self.instance.client.app.bsky.feed.get_actor_likes.side_effect = [
            mock.Mock(feed=[like_mock], cursor="next_cursor"),
            mock.Mock(feed=[like_mock], cursor=None)
        ]
        self.instance.client.app.bsky.feed.like.get.return_value = \
            mock.Mock(value=like_mock)

        result = list(self.instance.get_likes("2023-01-01"))
        assert len(result) == 2

    @pytest.mark.skip
    def test_get_likes_with_exceptions(self, setup_method):
        '''Test when an AtProtocolError is raised'''
        self.instance.client.app.bsky.feed.get_actor_likes.side_effect = \
            atproto_core.exceptions.AtProtocolError("Error")

        result = list(self.instance.get_likes("2023-01-01"))
        assert not result
        assert self.instance.logger.error.called

    @pytest.mark.skip
    def test_get_likes_failure_limit(self, setup_method):
        '''Test when the failure limit is reached'''
        self.instance.client.app.bsky.feed.get_actor_likes.side_effect = \
            atproto_core.exceptions.AtProtocolError("Error")

        result = list(self.instance.get_likes("2023-01-01"))
        assert not result
        assert self.instance.logger.error.called

    @pytest.mark.skip
    def test_get_likes_with_get_date(self, setup_method):
        '''Test when get_date is True'''
        like_mock = mock.Mock()
        like_mock.viewer.like = ("did", "rkey")
        like_mock.created_at = "2023-01-01T00:00:00Z"

        self.instance.client.app.bsky.feed.get_actor_likes.return_value = \
            mock.Mock(feed=[like_mock], cursor=None)
        self.instance.client.app.bsky.feed.like.get.return_value = \
            mock.Mock(value=like_mock)

        result = list(self.instance.get_likes("2023-01-01", get_date=True))
        assert len(result) == 1
        assert result[0].created_at == "2023-01-01T00:00:00Z"

    @pytest.mark.skip
    def test_get_likes_with_invalid_date(self, setup_method):
        '''Test when an invalid date is provided'''
        with pytest.raises(ValueError):
            list(self.instance.get_likes("invalid-date"))

    @pytest.mark.skip
    def test_get_likes_with_none_date_limit(self, setup_method):
        '''Test when date_limit_str is None'''
        like_mock = mock.Mock()
        like_mock.viewer.like = ("did", "rkey")
        like_mock.created_at = "2023-01-01T00:00:00Z"

        self.instance.client.app.bsky.feed.get_actor_likes.return_value = \
            mock.Mock(feed=[like_mock], cursor=None)
        self.instance.client.app.bsky.feed.like.get.return_value = \
            mock.Mock(value=like_mock)

        result = list(self.instance.get_likes(None))
        assert len(result) == 1
        assert result[0].created_at == "2023-01-01T00:00:00Z"

    @pytest.mark.skip
    def test_get_likes_with_empty_feed(self, setup_method):
        '''Test when the feed is empty'''
        self.instance.client.app.bsky.feed.get_actor_likes.return_value = \
            mock.Mock(feed=[], cursor=None)

        result = list(self.instance.get_likes("2023-01-01"))
        assert not result

    @pytest.mark.skip
    def test_get_likes_with_multiple_failures(self, setup_method):
        '''Test when multiple failures occur but within the limit'''
        self.instance.client.app.bsky.feed.get_actor_likes.side_effect = [
            atproto_core.exceptions.AtProtocolError("Error"),
            mock.Mock(feed=[], cursor=None)
        ]

        result = list(self.instance.get_likes("2023-01-01"))
        assert not result
        assert self.instance.logger.error.called

    def test_get_reposters(self, setup_method):
        '''Test the get_reposters method.'''
        mock_post = MagicMock()
        mock_post.repost_count = 1
        mock_post.uri = 'at://example/post/1'

        # Mock the response for get_posts
        with patch.object(self.instance, 'get_posts', return_value=[mock_post]):
            mock_reposter = MagicMock()
            mock_reposter.handle = 'reposter_user'
            mock_reposter.reposted_by = [mock_reposter]

            with patch.object(self.instance.client,
                              'get_reposted_by', return_value=mock_reposter):
                reposters = list(self.instance.get_reposters(
                                                        '@testuser.bsky.social'))
                assert len(reposters) == 1
                assert reposters[0]['profile'].handle == 'reposter_user'

    def test_post_text(self, setup_method):
        '''Test the post_text method.'''
        mock_post = MagicMock()
        mock_post.uri = 'at://example/post/1'

        with patch.object(self.instance.client, 'send_post', return_value=mock_post):
            uri = self.instance.post_text('Hello, BlueSky!')
            assert uri == 'at://example/post/1'

    def test_delete_post(self, setup_method):
        '''Test the delete_post method.'''
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(self.instance.client,
                          'delete_post', return_value=mock_response):
            response = self.instance.delete_post('at://example/post/1')
            assert response.status_code == 200

    def test_get_profile(self, setup_method):
        '''Test the get_profile method.'''
        mock_profile = MagicMock()
        mock_profile.did = 'did:example:123'

        with patch.object(self.instance.client,
                          'get_profile', return_value=mock_profile):
            profile = self.instance.get_profile('@testuser.bsky.social')
            assert profile.did == 'did:example:123'

    @pytest.mark.parametrize("handle, norm_handle", [
        (None, 'testuser.bsky.social'),
        ('testuser', 'testuser.bsky.social'),
        ('blah', 'blah.bsky.social'),
        ('@blah', 'blah.bsky.social'),
        ('blah.bsky.social', 'blah.bsky.social'),
        ('@blah.bsky.social', 'blah.bsky.social'),
        ('https://bsky.app/profile/testuser.bsky.social', 'testuser.bsky.social'),
        ('https://bsky.app/profile/other.bsky.social', 'other.bsky.social')
    ])
    def test_normalize_handle_value(self, setup_method, handle, norm_handle):
        '''Test BlueSky.normalize_handle_value method'''
        assert self.instance.normalize_handle_value(handle) == norm_handle
