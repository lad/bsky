#!/usr/bin/env python3
'''BlueSky command line interface: Base class for command classes'''

import dateparse


class BaseCmd:
    '''Base command for class which implement command line functions'''

    def __init__(self, bs, cmd_ns):
        self.bs = bs
        self.cmd_ns = cmd_ns

    def run(self):
        '''Run the command for the given command details passed to constructor'''
        getattr(self, self.cmd_ns.cmd.name)(*self.cmd_ns.func_args(self.cmd_ns))

    def print_profile(self, profile, label='Profile', full=False):
        '''Print details of the given profile structure'''
        self.print_profile_name(profile, label)
        if full:
            self.print_profile_link(profile)
            print(f"DID: {profile.did}")
            print(f"Created at: {dateparse.humanise_date_string(profile.created_at)}")
            if profile.description:
                print("Description:  ",
                      profile.description.replace("\n", "\n              "), "\n",
                      sep='')

    @staticmethod
    def print_profile_name(author, label='Profile'):
        '''Print the display name of the given profile'''
        if author.display_name:
            display_name = f"{author.display_name} "
        else:
            display_name = ''
        print(f"{label}: {display_name}@{author.handle}")

    @staticmethod
    def print_profile_link(author):
        '''Print the http link to the profile of the given user'''
        print(f"Profile Link: https://bsky.app/profile/{author.handle}")
