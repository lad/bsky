'''BlueSky tests'''

from unittest.mock import patch
import random
import string

import pytest

from mocks import BaseTest, MockUtils, setup_random_profile_names


class TestBuildPost(BaseTest):
    '''Test BlueSky rich() method'''
    def test_build_post(self, setup_random_profile_names):
        '''Test the build_post() method.'''
        # Allow .build_post() to use the real TextBuilder() class and assert
        # on what it returns
        input_text = 'Some text value'

        with patch.object(self.instance, 'profile_did',
                          side_effect=MockUtils.random_did()):
            tb = self.instance.build_post(input_text, setup_random_profile_names)
            built_text = tb.build_text()

            assert input_text in built_text
            for name in setup_random_profile_names:
                assert f"@{name}" in built_text
