'''Common base class for BlueSky test classes'''
from unittest.mock import patch

import pytest
import atproto_core

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
            mock_client_instance.login.return_value = None  # Mock the login method
            self.instance = BlueSky(handle='@testuser.bsky.social',
                                    password='testpassword')


class PartialFailure:
    '''Test class to simulate several atproto exceptions being raised
       but less than the failure limit. This will cause retries but not fail the
       operation'''
    def __init__(self, failure_limit, return_value):
        self.failure_limit = failure_limit
        self.return_value = return_value
        self.num_exceptions = 0

    def __call__(self, *args, **kwargs):
        self.num_exceptions += 1
        if self.num_exceptions < self.failure_limit:
            raise atproto_core.exceptions.AtProtocolError('Mocked Exception')
        return self.return_value
