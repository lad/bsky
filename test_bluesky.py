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

    @pytest.fixture(name='like_created_at')
    def setup_like_created_at(self):
        '''Create a timespec for reuse'''
        now = datetime.datetime.now(datetime.UTC)
        return now.isoformat(timespec='milliseconds')

    @pytest.fixture(name='like_mock')
    def setup_like_mock(self, like_created_at):
        '''Create a mock like object with a valid structure'''
        like_mock = MagicMock()
        like_mock.post = MagicMock()
        like_mock.post.viewer = MagicMock()
        like_mock.post.viewer.like = 'at://example/did/1'
        like_mock.post.uri = 'at://example/post/1'
        like_mock.created_at = like_created_at
        return like_mock

    @pytest.fixture(name='gal_mock_param', params=[1, 2, 3])
    def setup_gal_mock(self, request, like_mock):
        '''Create a mock response for get_actor_likes()'''
        gal_mock = MagicMock()
        gal_mock.feed = []
        # Number of like mocks depends on test fixture param
        for i in range(request.param):
            like_mock_copy = copy.deepcopy(like_mock)
            like_mock_copy.post.uri = f"at://example/post/{i}"
            gal_mock.feed.append(like_mock_copy)
        gal_mock.cursor = None
        return gal_mock, request.param

    @pytest.fixture(name='like_get_mock')
    def setup_like_get_mock(self, like_created_at):
        '''Create a mock response for like.get()'''
        like_get_mock = MagicMock()
        like_get_mock.value = MagicMock()
        like_get_mock.value.created_at = like_created_at
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

    def test_get_likes_no_date_no_count(self, setup_method, gal_mock_param, like_get_mock):
        '''Test the get_likes method, no date, no count, get_date default (false)'''
        # Mock the API call to return the mock response
        gal_mock, param = gal_mock_param
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes', return_value=gal_mock):

            # Call function under test: get_likes()Wwith no date and no count
            likes = list(self.instance.get_likes(None))
            assert len(likes) == param
            for like, mock_feed in zip(likes, gal_mock.feed):
                assert like.post.viewer.like == mock_feed.post.viewer.like
                assert like.post.uri == mock_feed.post.uri
                assert like.created_at is None

    def test_get_likes_no_date_no_count_get_date(self, setup_method,
                                                 gal_mock_param, like_get_mock):
        '''Test the get_likes method, no date, no count, get_date True'''
        # Mock the API call to return the mock response
        gal_mock, param = gal_mock_param
        with patch.object(self.instance.client.app.bsky.feed,
                          'get_actor_likes', return_value=gal_mock), \
            patch.object(self.instance.client.app.bsky.feed.like,
                         'get', return_value=like_get_mock):

            # Call function under test: get_likes()Wwith no date and no count
            likes = list(self.instance.get_likes(None, get_date=True))
            assert len(likes) == param
            for like, mock_feed in zip(likes, gal_mock.feed):
                assert like.post.viewer.like == mock_feed.post.viewer.like
                assert like.post.uri == mock_feed.post.uri
                assert like.created_at is not None
                assert like.created_at == mock_feed.created_at

    @pytest.mark.skip
    def test_get_likes_with_likes(self, setup_method):
        '''Test when likes are returned'''
        like_mock = mock.Mock()
        like_mock.viewer.like = ("did", "rkey")
        like_mock.created_at = "2023-01-01T00:00:00Z"

        self.instance.client.app.bsky.feed.get_actor_likes.return_value = \
            mock.Mock(feed=[like_mock], cursor=None)
        self.instance.client.app.bsky.feed.like.get.return_value = \
            mock.Mock(value=like_mock)

        result = list(self.instance.get_likes("2023-01-01"))
        assert len(result) == 1
        assert result[0].created_at == "2023-01-01T00:00:00Z"

    @pytest.mark.skip
    def test_get_likes_date_limit_reached(self, setup_method):
        '''Test when the date limit is reached'''
        like_mock = mock.Mock()
        like_mock.viewer.like = ("did", "rkey")
        like_mock.created_at = "2022-12-31T00:00:00Z"

        self.instance.client.app.bsky.feed.get_actor_likes.return_value = \
            mock.Mock(feed=[like_mock], cursor=None)
        self.instance.client.app.bsky.feed.like.get.return_value = \
            mock.Mock(value=like_mock)

        result = list(self.instance.get_likes("2023-01-01"))
        assert not result

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
        assert self.instance.logger.error.call_args[0][0] == "Giving up, " \
                                                             "more than %s failures"

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
