'''BlueSky tests'''

from unittest.mock import patch
from base_test import BaseTest


class TestBuildPost(BaseTest):
    '''Test BlueSky rich() method'''
    def test_build_post(self, setup_random_profile_names, random_did):
        '''Test the build_post() method.'''
        # Allow .build_post() to use the real TextBuilder() class and assert
        # on what it returns
        input_text = 'Some text value'

        with patch.object(self.instance, 'profile_did',
                          side_effect=random_did):
            tb = self.instance.build_post(input_text, setup_random_profile_names)
            built_text = tb.build_text()

            assert input_text in built_text
            for name in setup_random_profile_names:
                assert f"@{name}" in built_text
