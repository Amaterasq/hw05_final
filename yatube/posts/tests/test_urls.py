from http import HTTPStatus
from django.test import TestCase, Client
from django.urls.base import reverse

from posts.models import Post, Group, User
# from yatube.posts.tests.test_routes import ADD_COMMENT_URL

INDEX_URL = reverse('posts:index')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
LOGIN_URL = reverse('users:login')
POST_CREATE_URL = reverse('posts:post_create')
UNEXSISTING_PAGE_URL = 'unexsisting_page/'
USERNAME = 'StasBasov'
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
GROUP_SLUG = 'test-slug'
GROUP_LIST_URL = reverse('posts:group_list', args=[GROUP_SLUG])


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_of_post = User.objects.create_user(username='Ivan')
        cls.user = User.objects.create_user(username=USERNAME)
        cls.guest = Client()
        cls.another = Client()
        cls.another.force_login(cls.user)
        cls.author = Client()
        cls.author.force_login(cls.author_of_post)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        # Создадим пост
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author_of_post,
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            args=[cls.post.id]
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[cls.post.id]
        )
        cls.ADD_COMMENT_URL = reverse(
            'posts:add_comment',
            args=[cls.post.id]
        )
        cls.PROFILE_FOLLOW_URL = reverse(
            'posts:profile_follow',
            args=[cls.author_of_post]
        )
        cls.PROFILE_UNFOLLOW_URL = reverse(
            'posts:profile_unfollow',
            args=[cls.author_of_post]
        )

    # Проверяем доступность всех страниц
    def test_accessibility_address(self):
        urls_client_status = [
            [INDEX_URL, self.guest, HTTPStatus.OK],
            [GROUP_LIST_URL, self.guest, HTTPStatus.OK],
            [PROFILE_URL, self.guest, HTTPStatus.OK],
            [self.POST_DETAIL_URL, self.guest, HTTPStatus.OK],
            [UNEXSISTING_PAGE_URL, self.guest, HTTPStatus.NOT_FOUND],
            [POST_CREATE_URL, self.another, HTTPStatus.OK],
            [self.POST_EDIT_URL, self.author, HTTPStatus.OK],
            [POST_CREATE_URL, self.guest, HTTPStatus.FOUND],
            [self.POST_EDIT_URL, self.guest, HTTPStatus.FOUND],
            [self.POST_EDIT_URL, self.another, HTTPStatus.FOUND],
            [FOLLOW_INDEX_URL, self.another, HTTPStatus.OK],
            [self.ADD_COMMENT_URL, self.another, HTTPStatus.FOUND],
            [self.ADD_COMMENT_URL, self.author, HTTPStatus.FOUND],
            [self.ADD_COMMENT_URL, self.guest, HTTPStatus.FOUND],
            [self.PROFILE_FOLLOW_URL, self.another, HTTPStatus.FOUND],
            [self.PROFILE_FOLLOW_URL, self.author, HTTPStatus.FOUND],
            [self.PROFILE_FOLLOW_URL, self.guest, HTTPStatus.FOUND],
            [self.PROFILE_UNFOLLOW_URL, self.another, HTTPStatus.FOUND],
            [self.PROFILE_UNFOLLOW_URL, self.author, HTTPStatus.NOT_FOUND],
            [self.PROFILE_UNFOLLOW_URL, self.guest, HTTPStatus.FOUND],

        ]
        for url, client, code in urls_client_status:
            with self.subTest(url=url, client=client, code=code):
                self.assertEqual(
                    client.get(url).status_code,
                    code
                )

    # Проверяем шаблоны для всех страниц
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls_templates = [
            [INDEX_URL, 'posts/index.html'],
            [POST_CREATE_URL, 'posts/create_post.html'],
            [GROUP_LIST_URL, 'posts/group_list.html'],
            [PROFILE_URL, 'posts/profile.html'],
            [self.POST_DETAIL_URL, 'posts/post_detail.html'],
            [self.POST_EDIT_URL, 'posts/create_post.html'],
            [FOLLOW_INDEX_URL, 'posts/follow.html'],
        ]
        for url, template in urls_templates:
            with self.subTest(url=url, template=template):
                self.assertTemplateUsed(
                    self.author.get(url, follow=True),
                    template
                )

    # Проверяем редиректы
    def test_url_client_redirects(self):
        url_redirect = [
            [POST_CREATE_URL, self.guest,
             f'{LOGIN_URL}?next={POST_CREATE_URL}'],
            [self.POST_EDIT_URL, self.guest,
             f'{LOGIN_URL}?next={self.POST_EDIT_URL}'],
            [self.POST_EDIT_URL, self.another, self.POST_DETAIL_URL],
            [self.ADD_COMMENT_URL, self.guest,
             f'{LOGIN_URL}?next={self.ADD_COMMENT_URL}'],
            [self.PROFILE_FOLLOW_URL, self.guest,
             f'{LOGIN_URL}?next={self.PROFILE_FOLLOW_URL}'],
            [self.PROFILE_UNFOLLOW_URL, self.guest,
             f'{LOGIN_URL}?next={self.PROFILE_UNFOLLOW_URL}'],
        ]
        for url, client, redirect in url_redirect:
            with self.subTest(url=url, client=client, redirect=redirect):
                self.assertRedirects(
                    client.get(url),
                    redirect
                )
