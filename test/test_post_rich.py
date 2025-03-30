'''BlueSky tests'''

from unittest.mock import patch, MagicMock
import random
import string

import atproto_core
import pytest

import mocks


class TestPostRich(mocks.BaseTest):
    '''Test BlueSky rich() method'''
    def random_profile_name(self):
        '''Return an random fake profile name'''
        return f"{''.join(random.sample(string.ascii_letters, 16))}" \
               f"{random.randint(20000, 100000)}" \
               f".bsky.social"

    @pytest.fixture(params=range(1, 11))
    def setup_random_profile_names(self, request):
        '''Return a list of random profile names'''
        return [self.random_profile_name()] * request.param

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
                          side_effect=mocks.PartialFailure(
                              self.instance.FAILURE_LIMIT, mock_post)) \
                                      as mock_send_post, \
             patch.object(self.instance, 'build_post', return_value=mock_text):
            uri = self.instance.post_rich('Hello', setup_random_profile_names)
            assert uri == mock_post.uri
            assert mock_send_post.call_count == self.instance.FAILURE_LIMIT
