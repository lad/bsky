#!/usr/bin/env python3
'''BlueSky command line interface: Msg command class'''

from blueskycmd import BaseCmd
import dateparse


class Msg(BaseCmd):
    '''BlueSky command line interface: Msg command class'''

    def unread(self):
        '''Print a count of the unread notifications'''
        count = self.bs.get_unread_notifications_count()
        print(f"Unread: {count}")

    def gets(self, date_limit, show_all, count_limit, mark):
        '''Print the unread, or all, notifications received, optionally since the
           date supplied. Optionally mark the unread notifications as read'''
        notification_count, unread_count = 0, 0
        for notif, post in self.bs.get_notifications(date_limit_str=date_limit,
                                                     count_limit=count_limit,
                                                     mark_read=mark, get_all=show_all):
            if show_all or not notif.is_read:
                self.print_notification_entry(notif, post)

            if not notif.is_read:
                unread_count += 1
            notification_count += 1

        print(f"{notification_count} notifications, "
              f"{notification_count - unread_count} read, "
              f"{unread_count} unread")

    def print_notification_entry(self, notif, post):
        '''Print details of the given notification structure'''
        self.print_profile_name(notif.author)
        self.print_profile_link(notif.author)
        print(f"Reason: {notif.reason}")
        print(f"Date: {dateparse.humanise_date_string(notif.indexed_at)}")
        if post:
            print(f"Post: {post.value.text}")
        if hasattr(notif.record, 'text'):
            print(f"Reply: {notif.record.text}")
        print('-----')
