'''BlueSky tests'''

import pytest

from base_test import BaseTest


class TestNormalizeHandleValues(BaseTest):
    '''Test BlueSky get_likes() method'''
    @pytest.mark.parametrize("handle, norm_handle", [
        (None, 'testuser.bsky.social'),
        ('testuser', 'testuser.bsky.social'),
        ('blah', 'blah.bsky.social'),
        ('@blah', 'blah.bsky.social'),
        ('blah.bsky.social', 'blah.bsky.social'),
        ('@blah.bsky.social', 'blah.bsky.social'),
        ('https://bsky.app/profile/testuser.bsky.social', 'testuser.bsky.social'),
        ('https://bsky.app/profile/other.bsky.social', 'other.bsky.social'),
        ('did:plc:alcvibl27vueaibfl7b5oeqg', 'did:plc:alcvibl27vueaibfl7b5oeqg'),
        ('did:plc:lkajsdljkasd', 'did:plc:lkajsdljkasd')
    ])
    def test_normalize_handle_value(self, handle, norm_handle):
        '''Test BlueSky.normalize_handle_value method'''
        assert self.instance.normalize_handle_value(handle) == norm_handle
