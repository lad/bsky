'''BlueSky tests'''

from unittest.mock import patch
import random
import string

import pytest

from base_test import BaseTest


class TestBuildPost(BaseTest):
    '''Test BlueSky rich() method'''
    def random_profile_name(self):
        '''Return an random fake profile name'''
        return f"{''.join(random.sample(string.ascii_letters, 16))}" \
               f"{random.randint(20000, 100000)}" \
               f".bsky.social"

    def random_did(self):
        '''Return an random fake DID'''
        return f"did:plc:{''.join(random.sample(string.ascii_letters, 24))}"

    @pytest.fixture(params=range(1, 11))
    def setup_random_profile_names(self, request):
        '''Return a list of random profile names'''
        return [self.random_profile_name()] * request.param

    def test_build_post(self, setup_random_profile_names):
        '''Test the build_post() method.'''
        # Allow .build_post() to use the real TextBuilder() class and assert
        # on what it returns
        input_text = 'Some text value'

        with patch.object(self.instance, 'profile_did',
                          side_effect=self.random_did()):
            tb = self.instance.build_post(input_text, setup_random_profile_names)
            built_text = tb.build_text()

            assert input_text in built_text
            for name in setup_random_profile_names:
                assert f"@{name}" in built_text
