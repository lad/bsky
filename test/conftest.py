'''Utilities for pytest tests'''
import sys
from pathlib import Path

from unittest.mock import MagicMock
import random
import string

import pytest

# pytest init for python include path'''
sys.path.append(str(Path(__file__).resolve().parent.parent))


class MockUtils:
    '''Various helper methods for building mocks and fixtures'''
    @staticmethod
    def random_profile_name():
        '''Return an random fake profile name'''
        return f"{''.join(random.sample(string.ascii_letters, 16))}" \
               f"{random.randint(20000, 100000)}" \
               f".bsky.social"

    @staticmethod
    def profile(handle_name):
        '''Mock an atproto BlueSky profile object'''
        mock = MagicMock()
        mock.handle = handle_name
        return mock


@pytest.fixture
def setup_random_profile_name():
    '''pytest fixture to create a random BlueSky profile name'''
    return MockUtils.random_profile_name()


@pytest.fixture(params=range(1, 11))
def setup_random_profile_names(request):
    '''Return a list of random profile names'''
    return [MockUtils.random_profile_name()] * request.param


@pytest.fixture
def random_did():
    '''Return an random fake DID'''
    return f"did:plc:{''.join(random.sample(string.ascii_letters, 24))}"
