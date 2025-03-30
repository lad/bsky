'''BlueSky tests'''

from unittest.mock import patch, MagicMock

import mocks


class TestGetReposters(mocks.BaseTest):
    '''Test BlueSky get_reposters() method'''
    def test_get_reposters(self):
        '''Test the get_reposters() method.'''
        mock_post = MagicMock()
        mock_post.repost_count = 1
        mock_post.uri = 'at://example/post/1'

        with patch.object(self.instance, 'get_posts', return_value=[mock_post]):
            mock_reposter = MagicMock()
            mock_reposter.handle = 'reposter_user'
            mock_reposter.reposted_by = [mock_reposter]

            with patch.object(self.instance.client,
                              'get_reposted_by', return_value=mock_reposter):
                reposters = list(self.instance.get_reposters(
                                                        '@testuser.bsky.social'))
                assert len(reposters) == 1
                assert reposters[0]['profile'].handle == 'reposter_user'
