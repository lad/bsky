'''Common base class for BlueSky test classes'''
from unittest.mock import patch

import pytest
from bluesky import BlueSky

# pylint: disable=W0201 (attribute-defined-outside-init)
# pylint: disable=R0903 (too-few-public-methods)


class BaseTest:
    '''Common base class for BlueSky test classes'''
    @pytest.fixture(autouse=True)
    def setup(self):
        '''Create an instance of the class containing the get_likes method'''
        with patch('atproto.Client') as mock_client:
            mock_client_instance = mock_client.return_value
            mock_client_instance.login.return_value = None  # Mock the login method
            self.instance = BlueSky(handle='@testuser.bsky.social',
                                    password='testpassword')
