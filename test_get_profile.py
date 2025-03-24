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

    def test_get_profile(self, setup_method):
        '''Test the get_profile method.'''
        mock_profile = MagicMock()
        mock_profile.did = 'did:example:123'

        with patch.object(self.instance.client,
                          'get_profile', return_value=mock_profile):
            profile = self.instance.get_profile('@testuser.bsky.social')
            assert profile.did == 'did:example:123'
