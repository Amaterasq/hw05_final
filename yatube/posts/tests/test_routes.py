from django.test import TestCase
from django.urls.base import reverse


USERNAME = 'StasBasov'
SLUG = 'test-slug'
POST_ID = 1


class RoutesURLTests(TestCase):

    def test_routes(self):
        urls = [
            ['index', [], '/'],
            ['post_create', [], '/create/'],
            ['group_list', [SLUG], f'/group/{SLUG}/'],
            ['profile', [USERNAME], f'/profile/{USERNAME}/'],
            ['post_detail', [POST_ID], f'/posts/{POST_ID}/'],
            ['post_edit', [POST_ID], f'/posts/{POST_ID}/edit/'],
            ['add_comment', [POST_ID], f'/posts/{POST_ID}/comment/'],
            ['follow_index', [], '/follow/'],
            ['profile_follow', [USERNAME], f'/profile/{USERNAME}/follow/'],
            ['profile_unfollow', [USERNAME], f'/profile/{USERNAME}/unfollow/'],
        ]
        for name, params, expected_url in urls:
            with self.subTest(name=name):
                self.assertEqual(
                    reverse(f'posts:{name}', args=params),
                    expected_url
                )
