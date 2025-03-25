'''BlueSky tests'''

from unittest.mock import patch, MagicMock

from base_test import BaseTest


class TestPostText(BaseTest):
    '''Test BlueSky post_text() method'''
    def test_post_text(self):
        '''Test the post_text() method.'''
        mock_post = MagicMock()
        mock_post.uri = 'at://example/post/1'

        with patch.object(self.instance.client, 'send_post', return_value=mock_post):
            uri = self.instance.post_text('Hello, BlueSky!')
            assert uri == 'at://example/post/1'
