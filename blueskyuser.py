#!/usr/bin/env python3
'''BlueSky command line interface: User command class'''

from blueskycmd import BaseCmd


class User(BaseCmd):
    '''BlueSky command line interface: User command class'''

    def did(self, handle):
        """Print the DID of the given user"""
        hand = handle or self.bs.handle
        if '.' not in hand:
            hand += '.bsky.social'
        did = self.bs.profile_did(hand)
        if did:
            print(did)
        else:
            print(f"No DID found for {hand}")

    def profile(self, handle):
        """Print the profile entry of the given user handle"""
        profile = self.bs.get_profile(handle)
        if profile:
            self.print_profile(profile, full=True)
        else:
            print(f"{handle} profile not found")
