'''Common base class for BlueSky test classes'''
from unittest.mock import patch
import random
import string

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


class MockUtils:
    '''Various convenience methods for building mocks or mock data'''
    @staticmethod
    def random_profile_name():
        '''Return an random fake profile name'''
        return f"{''.join(random.sample(string.ascii_letters, 16))}" \
               f"{random.randint(20000, 100000)}" \
               f".bsky.social"

    @staticmethod
    def random_did():
        '''Return an random fake DID'''
        return f"did:plc:{''.join(random.sample(string.ascii_letters, 24))}"


@pytest.fixture(params=range(1, 11))
def setup_random_profile_names(request):
    '''Return a list of random profile names'''
    return [MockUtils.random_profile_name()] * request.param
