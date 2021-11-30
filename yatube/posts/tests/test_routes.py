from django.test import TestCase
from django.urls.base import reverse


INDEX_URL = 'index'
POST_CREATE_URL = 'post_create'
USERNAME = 'StasBasov'
PROFILE_URL = 'profile'
SLUG = 'test-slug'
GROUP_LIST_URL = 'group_list'
POST_ID = 1
POST_DETAIL_URL = 'post_detail'
POST_EDIT_URL = 'post_edit'
ADD_COMMENT_URL = 'add_comment'
FOLLOW_INDEX_URL = 'follow_index'
PROFILE_FOLLOW_URL = 'profile_follow'
PROFILE_UNFOLLOW_URL = 'profile_unfollow'


class RoutesURLTests(TestCase):

    def test_routes(self):
        urls = [
            [INDEX_URL, [], '/'],
            [POST_CREATE_URL, [], '/create/'],
            [GROUP_LIST_URL, [SLUG], f'/group/{SLUG}/'],
            [PROFILE_URL, [USERNAME], f'/profile/{USERNAME}/'],
            [POST_DETAIL_URL, [POST_ID], f'/posts/{POST_ID}/'],
            [POST_EDIT_URL, [POST_ID], f'/posts/{POST_ID}/edit/'],
            [ADD_COMMENT_URL, [POST_ID], f'/posts/{POST_ID}/comment/'],
            [FOLLOW_INDEX_URL, [], '/follow/'],
            [PROFILE_FOLLOW_URL, [USERNAME], f'/profile/{USERNAME}/follow/'],
            [
                PROFILE_UNFOLLOW_URL,
                [USERNAME],
                f'/profile/{USERNAME}/unfollow/'
            ],
        ]
        for url, param, expected_url in urls:
            with self.subTest(url=url):
                self.assertEqual(
                    reverse('posts:' + url, args=param),
                    expected_url
                )
