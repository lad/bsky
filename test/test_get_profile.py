'''BlueSky tests'''

from unittest.mock import patch, MagicMock

from base_test import BaseTest


class TestGetProfile(BaseTest):
    '''Test BlueSky get_profile() method'''
    def test_get_profile(self):
        '''Test the get_profile() method.'''
        mock_profile = MagicMock()
        mock_profile.did = 'did:example:123'

        with patch.object(self.instance.client,
                          'get_profile', return_value=mock_profile):
            profile = self.instance.get_profile('@testuser.bsky.social')
            assert profile.did == 'did:example:123'
