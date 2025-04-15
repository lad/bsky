'''Common base class for BlueSky test classes'''

from unittest.mock import patch, Mock
import pytest
from bluesky import BlueSky

# pylint: disable=W0201 (attribute-defined-outside-init)
# pylint: disable=R0903 (too-few-public-methods)


class BaseTest:
    '''Common base class for BlueSky test classes'''
    @pytest.fixture(autouse=True)
    def setup(self):
        '''Create an instance of the BlueSky class mocking out the login method'''
        with patch('atproto.Client') as mock_client:
            mock_client_instance = mock_client.return_value
            # Mock the login method
            mock_client_instance.login.return_value = None
            self.instance = BlueSky(handle='@testuser.bsky.social',
                                    password='testpassword')

            # Mock its atproto client
            self.instance._client = mock_client
