'''BlueSky tests'''

from unittest.mock import patch
import random
import string

import pytest

from mocks import BaseTest, random_profile_names, random_did


class TestBuildPost(BaseTest):
    '''Test BlueSky rich() method'''
    def test_build_post(self, random_profile_names, random_did):
        '''Test the build_post() method.'''
        # Allow .build_post() to use the real TextBuilder() class and assert
        # on what it returns
        input_text = 'Some text value'

        with patch.object(self.instance, 'profile_did',
                          side_effect=random_did):
            tb = self.instance.build_post(input_text, random_profile_names)
            built_text = tb.build_text()

            assert input_text in built_text
            for name in random_profile_names:
                assert f"@{name}" in built_text
