'''BlueSky tests'''

from unittest.mock import patch, MagicMock

import pytest
from bluesky import BlueSky

# pylint: disable=W0613 (unused-argument)
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

    def test_delete_post(self, setup_method):
        '''Test the delete_post method.'''
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(self.instance.client,
                          'delete_post', return_value=mock_response):
            response = self.instance.delete_post('at://example/post/1')
            assert response.status_code == 200
