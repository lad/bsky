'''Test login that happens when BlueSky class is instantiated.'''
from unittest.mock import patch

import atproto_core

import pytest
from partial_failure import PartialFailure

from bluesky import BlueSky


# pylint: disable=W0201 (attribute-defined-outside-init)
# pylint: disable=R0903 (too-few-public-methods)


class TestBlueSkyLogin:
    '''Test BlueSky login failures'''

    @patch('atproto.Client')
    def test_login_with_exception_failures(self, mock_client):
        '''Test the BlueSky instantation/login with exception failures'''
        mock_client_instance = mock_client.return_value
        mock_client_instance.login.side_effect = \
            atproto_core.exceptions.AtProtocolError('Mocked Exception')

        with pytest.raises(IOError):
            self.instance = BlueSky(handle='@testuser.bsky.social',
                                    password='testpassword')

        assert mock_client_instance.login.call_count == BlueSky.FAILURE_LIMIT

    @patch('atproto.Client')
    def test_login_with_retries(self, mock_client):
        '''Test the BlueSky instantation/login with partial failure causing retries'''
        mock_client_instance = mock_client.return_value
        mock_client_instance.login.side_effect = \
            PartialFailure(BlueSky.FAILURE_LIMIT, None)

        handle = '@testuser.bsky.social'
        password = 'testpassword'
        self.instance = BlueSky(handle=handle, password=password)

        assert self.instance
        assert self.instance.handle == handle
        assert mock_client_instance.login.call_count == BlueSky.FAILURE_LIMIT
