'''BlueSky tests'''

from unittest.mock import patch, MagicMock

import atproto_core
import pytest

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

    def test_get_profile_exception_limit(self):
        with patch.object(self.instance.client,
                          'get_profile', 
                          side_effect=atproto_core.exceptions.AtProtocolError(
                              'Mocked Exception')) as exception_mock:
            with pytest.raises(IOError):
                self.instance.get_profile('anyhandle')
            assert exception_mock.call_count == self.instance.FAILURE_LIMIT
