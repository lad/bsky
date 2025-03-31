'''BlueSky tests'''

from unittest.mock import patch, MagicMock

import atproto_core
import pytest
from base_test import BaseTest
from partial_failure import PartialFailure


class TestPostText(BaseTest):
    '''Test BlueSky post_text() method'''
    def test_post_text(self):
        '''Test the post_text() method.'''
        mock_post = MagicMock()
        mock_post.uri = 'at://example/post/1'

        with patch.object(self.instance.client, 'send_post', return_value=mock_post):
            uri = self.instance.post_text('Hello')
            assert uri == mock_post.uri

    def test_post_text_exception_limit(self):
        '''Test the post_text() method with exceptions failure'''
        with patch.object(self.instance.client, 'send_post',
                          side_effect=atproto_core.exceptions.AtProtocolError(
                              'Mocked Exception')) as mock_exception:
            with pytest.raises(IOError):
                self.instance.post_text('Hello')
            assert mock_exception.call_count == self.instance.FAILURE_LIMIT

    def test_post_text_with_retries(self):
        '''Test the post_text() method with exceptions partial failure causing
           retries'''
        mock_post = MagicMock()
        mock_post.uri = 'at://example/post/1'

        with patch.object(self.instance.client, 'send_post',
                          side_effect=PartialFailure(self.instance.FAILURE_LIMIT,
                                                     mock_post)) as mock_exception:
            uri = self.instance.post_text('Hello')
            assert uri == mock_post.uri
            assert mock_exception.call_count == self.instance.FAILURE_LIMIT
