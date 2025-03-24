'''BlueSky tests'''

from unittest.mock import patch

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

    @pytest.mark.parametrize("handle, norm_handle", [
        (None, 'testuser.bsky.social'),
        ('testuser', 'testuser.bsky.social'),
        ('blah', 'blah.bsky.social'),
        ('@blah', 'blah.bsky.social'),
        ('blah.bsky.social', 'blah.bsky.social'),
        ('@blah.bsky.social', 'blah.bsky.social'),
        ('https://bsky.app/profile/testuser.bsky.social', 'testuser.bsky.social'),
        ('https://bsky.app/profile/other.bsky.social', 'other.bsky.social'),
        ('did:plc:alcvibl27vueaibfl7b5oeqg', 'did:plc:alcvibl27vueaibfl7b5oeqg'),
        ('did:plc:lkajsdljkasd', 'did:plc:lkajsdljkasd')
    ])
    def test_normalize_handle_value(self, setup_method, handle, norm_handle):
        '''Test BlueSky.normalize_handle_value method'''
        assert self.instance.normalize_handle_value(handle) == norm_handle
