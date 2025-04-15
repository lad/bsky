'''Test login that happens when BlueSky class is instantiated.'''
from unittest.mock import patch

import atproto_core
import pytest
from partial_failure import PartialFailure
from bluesky import BlueSky

# pylint: disable=W0201 (attribute-defined-outside-init)


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
            # Have to touch .client to have BlueSky() attempt to login
            assert self.instance.client

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
        # Have to touch .client to have BlueSky() attempt to login
        assert self.instance.client
        assert self.instance.handle == handle
        assert mock_client_instance.login.call_count == BlueSky.FAILURE_LIMIT
