'''BlueSky tests'''

import atproto_core
import pytest

from base_test import BaseTest
from partial_failure import PartialFailure


class TestGetUnreadNotificationCount(BaseTest):
    '''Test BlueSky get_unread_notifications_count() method'''
    @pytest.mark.parametrize('count', range(1, 11))
    def test_get_unread_notification_count(self, count):
        '''Test unread notification count'''
        self.instance.client.app.bsky.notification.get_unread_count.return_value = \
            count

        assert self.instance.get_unread_notifications_count() == count

    def test_get_unread_notification_count_exception_limit(self):
        '''Test the get_unread_notifications_count_cmd() method with exceptions
           failure'''
        guc = self.instance.client.app.bsky.notification.get_unread_count
        guc.side_effect = atproto_core.exceptions.AtProtocolError('Mocked Exception')
        with pytest.raises(IOError):
            self.instance.get_unread_notifications_count()
        assert guc.call_count == self.instance.FAILURE_LIMIT

    @pytest.mark.parametrize('count', range(1, 11))
    def test_get_unread_notification_count_with_retries(self, count):
        '''Test get_unread_notifications_count_cmd() method with exceptions partial
           failure causing retries'''
        guc = self.instance.client.app.bsky.notification.get_unread_count
        guc.side_effect = PartialFailure(self.instance.FAILURE_LIMIT, count)
        assert self.instance.get_unread_notifications_count() == count
