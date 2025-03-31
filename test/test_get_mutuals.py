'''Tests for the BlueSky.get_mutuals() method'''

from unittest.mock import patch
from dataclasses import dataclass

import pytest
from conftest import MockUtils
from base_test import BaseTest

# pylint: disable=R0903 (too-few-public-methods)


@dataclass
class FollowsFollowersMutuals:
    '''Encapulate test data for testing BlueSky.get_mutuals()'''
    follows: list
    followers: list
    follows_not_followers: list
    followers_not_follows: list
    both: list


class TestData:
    '''Some basic test data for testing get_mutuals()'''
    FOLLOWS_FOLLOWERS_MUTUALS_1 = [FollowsFollowersMutuals([], [], [], [], [])]
    FOLLOWS_FOLLOWERS_MUTUALS_2 = [FollowsFollowersMutuals(
            [MockUtils.profile('handle1'), MockUtils.profile('handle2'),
             MockUtils.profile('handle3'), MockUtils.profile('handle4'),
             MockUtils.profile('handle5')],

            [MockUtils.profile('handle1'), MockUtils.profile('handle2'),
             MockUtils.profile('handle5'), MockUtils.profile('handle6'),
             MockUtils.profile('handle7'), MockUtils.profile('handle8')],

            ['handle3', 'handle4'],                 # follows_not_followers
            ['handle6', 'handle7', 'handle8'],      # followers_not_follows
            ['handle1', 'handle2', 'handle5'])]     # both follows and followers


class TestGetMutuals(BaseTest):
    '''Tests for the BlueSky.get_mutuals() method'''
    @staticmethod
    def generate_test_data():
        '''Generate a more complex set of test data'''
        follows_range = list(range(1, 101))
        followers_range = list(range(51, 201))
        follows_not_followers_range = list(range(1, 51))
        followers_not_follows_range = list(range(101, 201))
        both_range = list(range(51, 101))

        # Remove a few parts of the range here and there
        for i in range(13, 21):
            follows_range.remove(i)
            follows_not_followers_range.remove(i)
        for i in range(113, 121):
            followers_range.remove(i)
            followers_not_follows_range.remove(i)
        follows_range.remove(90)
        followers_range.remove(90)
        both_range.remove(90)

        # Create the mocks and handles to test against
        follows = [MockUtils.profile(f"handle{i}") for i in follows_range]
        followers = [MockUtils.profile(f"handle{i}") for i in followers_range]
        follows_not_followers = [f"handle{i}" for i in follows_not_followers_range]
        followers_not_follows = [f"handle{i}" for i in followers_not_follows_range]
        both = [f"handle{i}" for i in both_range]

        return [[FollowsFollowersMutuals(follows, followers, follows_not_followers,
                                         followers_not_follows, both)],
                TestData.FOLLOWS_FOLLOWERS_MUTUALS_1,
                TestData.FOLLOWS_FOLLOWERS_MUTUALS_2]

    @pytest.mark.parametrize('flag', ['both', 'follows-not-followers',
                                      'followers-not-follows'])
    @pytest.mark.parametrize('testdata', generate_test_data())
    def test_get_mutuals_none(self, flag, testdata, setup_random_profile_name):
        '''Test BlueSky.get_likes() when get_actor_likes() raises exceptions'''
        for ffm in testdata:
            with patch.object(self.instance, 'follows', return_value=ffm.follows), \
                 patch.object(self.instance, 'followers', return_value=ffm.followers):
                # get_mutuals() is a generator, use list() to ensure it is
                # actually invoked
                result = list(self.instance.get_mutuals(setup_random_profile_name,
                                                        flag))
                handles = sorted([p.handle for p in result],
                                 key=lambda s: int(s[6:]))

                if flag == 'follows-not-followers':
                    assert handles == ffm.follows_not_followers
                elif flag == 'followers-not-follows':
                    assert handles == ffm.followers_not_follows
                elif flag == 'both':
                    assert handles == ffm.both
                else:
                    assert False
