'''BlueSky tests'''

from unittest.mock import patch, MagicMock

import atproto_core
import pytest
from base_test import BaseTest
from partial_failure import PartialFailure


class TestPostRich(BaseTest):
    '''Test BlueSky.post_rich() method'''
    def test_post_rich(self, setup_random_profile_names):
        '''Test the post_rich() method.'''
        mock_post = MagicMock()
        mock_post.uri = 'at://example/post/1'
        mock_text = 'some mock rich text\n@handle\nhttps://example.com/foo/bar/\n'

        with patch.object(self.instance.client, 'send_post', return_value=mock_post) \
                as mock_send_post, \
             patch.object(self.instance, 'build_post', return_value=mock_text):
            uri = self.instance.post_rich('Hello', setup_random_profile_names)
            assert uri == mock_post.uri
            assert mock_send_post.call_args[0][0] == mock_text

    def test_post_rich_exception_limit(self, setup_random_profile_names):
        '''Test the rich() method with exception failure'''
        mock_text = 'some mock rich text\n@handle\nhttps://example.com/foo/bar/\n'

        with patch.object(self.instance.client, 'send_post',
                          side_effect=atproto_core.exceptions.AtProtocolError(
                              'Mocked Exception')) as mock_exception, \
             patch.object(self.instance, 'build_post', return_value=mock_text):
            with pytest.raises(IOError):
                self.instance.post_rich('Hello', setup_random_profile_names)
            assert mock_exception.call_count == self.instance.FAILURE_LIMIT

    def test_post_rich_with_retries(self, setup_random_profile_names):
        '''Test the rich() method with exceptions partial failure causing
           retries'''
        mock_post = MagicMock()
        mock_post.uri = 'at://example/post/1'
        mock_text = 'some mock rich text\n@handle\nhttps://example.com/foo/bar/\n'

        with patch.object(self.instance.client, 'send_post',
                          side_effect=PartialFailure(self.instance.FAILURE_LIMIT,
                                                     mock_post)) as mock_send_post, \
             patch.object(self.instance, 'build_post', return_value=mock_text):
            uri = self.instance.post_rich('Hello', setup_random_profile_names)
            assert uri == mock_post.uri
            assert mock_send_post.call_count == self.instance.FAILURE_LIMIT
