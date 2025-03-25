'''BlueSky tests'''

from unittest.mock import patch
import pytest

import atproto_core

from base_test import BaseTest

# pylint: disable=W0613 (unused-argument)
# pylint: disable=W0201 (attribute-defined-outside-init)


class TestDeletePost(BaseTest):
    '''Test BlueSky delete_post() method for return values'''
    @pytest.mark.parametrize("return_value", [True, False])
    def test_delete_post(self, return_value):
        '''Test the delete_post() method.'''
        with patch.object(self.instance.client,
                          'delete_post', return_value=return_value):
            response = self.instance.delete_post('at://example/post/1')
            assert response == return_value

    def test_delete_post_failed(self):
        '''Test the delete_post() method for failed delete with exceptions'''
        self.num_exceptions = 0
        def side_effect_atproto_exception(*args, **kwargs):
            self.num_exceptions += 1
            raise atproto_core.exceptions.AtProtocolError('Mocked Exception')

        with patch.object(self.instance.client,
                          'delete_post', return_value=False,
                          side_effect=side_effect_atproto_exception):
            response = self.instance.delete_post('at://example/post/1')
            assert not response
            assert self.num_exceptions == self.instance.FAILURE_LIMIT

    def test_delete_post_partial_failure(self):
        '''Test the delete_post() method for successful delete with some exceptions'''
        self.num_exceptions = 0
        def side_effect_atproto_exception(*args, **kwargs):
            self.num_exceptions += 1
            if self.num_exceptions < self.instance.FAILURE_LIMIT - 1:
                raise atproto_core.exceptions.AtProtocolError('Mocked Exception')

            return True

        with patch.object(self.instance.client,
                          'delete_post', return_value=False,
                          side_effect=side_effect_atproto_exception):
            response = self.instance.delete_post('at://example/post/1')
            assert response
