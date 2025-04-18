'''BlueSky tests'''

from unittest.mock import patch
import pytest
import atproto_core
from base_test import BaseTest
from partial_failure import PartialFailure


class TestDeletePost(BaseTest):
    '''Test BlueSky delete_post() method for return values'''
    def test_delete_post_succeeded(self):
        '''Test the delete_post() method.'''
        with patch.object(self.instance.client,
                          'delete_post', return_value=True):
            response = self.instance.delete_post('at://example/post/1')
            assert response

    def test_delete_post_failed(self):
        '''Test the delete_post() method for failed delete with exceptions'''
        with patch.object(self.instance.client,
                          'delete_post', return_value=False,
                          side_effect=atproto_core.exceptions.AtProtocolError(
                              'Mocked Exception')):
            with pytest.raises(IOError):
                self.instance.delete_post('at://example/post/1')

    def test_delete_post_partial_failure(self):
        '''Test the delete_post() method for successful delete with some exceptions'''
        with patch.object(self.instance.client,
                          'delete_post', return_value=False,
                          side_effect=PartialFailure(self.instance.FAILURE_LIMIT,
                                                     True)):
            response = self.instance.delete_post('at://example/post/1')
            assert response
