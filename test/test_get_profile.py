'''BlueSky tests'''

from unittest.mock import patch, MagicMock

import atproto_core
import pytest

import mocks


class TestGetProfile(mocks.BaseTest):
    '''Test BlueSky get_profile() method'''
    def test_get_profile(self):
        '''Test the get_profile() method.'''
        mock_profile = MagicMock()
        mock_profile.did = 'did:example:123'

        with patch.object(self.instance.client,
                          'get_profile', return_value=mock_profile):
            profile = self.instance.get_profile('@testuser.bsky.social')
            assert profile.did == mock_profile.did

    def test_get_profile_exception_limit(self):
        '''Test the get_profile() method with exceptions failure'''
        with patch.object(self.instance.client,
                          'get_profile',
                          side_effect=atproto_core.exceptions.AtProtocolError(
                              'Mocked Exception')) as mock_exception:
            with pytest.raises(IOError):
                self.instance.get_profile('anyhandle')
            assert mock_exception.call_count == self.instance.FAILURE_LIMIT

    def test_get_profile_with_retries(self):
        '''Test the get_profile() method with exceptions partial failure causing
           retries'''
        mock_profile = MagicMock()
        mock_profile.did = 'did:example:123'

        with patch.object(self.instance.client,
                          'get_profile',
                          side_effect=mocks.PartialFailure(
                              self.instance.FAILURE_LIMIT, mock_profile)) \
                                      as mock_exception:
            profile = self.instance.get_profile('anyhandle')
            assert profile.did == mock_profile.did
            assert mock_exception.call_count == self.instance.FAILURE_LIMIT
