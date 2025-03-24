'''BlueSky tests'''

from unittest.mock import patch, MagicMock

from base_test import BaseTest

# pylint: disable=W0613 (unused-argument)
# pylint: disable=W0201 (attribute-defined-outside-init)


class TestDeletePost(BaseTest):
    '''Test BlueSky get_likes() method'''
    def test_delete_post(self):
        '''Test the delete_post method.'''
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(self.instance.client,
                          'delete_post', return_value=mock_response):
            response = self.instance.delete_post('at://example/post/1')
            assert response.status_code == 200
