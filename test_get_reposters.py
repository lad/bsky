'''BlueSky tests'''

from unittest.mock import patch, MagicMock

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

    def test_get_reposters(self, setup_method):
        '''Test the get_reposters method.'''
        mock_post = MagicMock()
        mock_post.repost_count = 1
        mock_post.uri = 'at://example/post/1'

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
