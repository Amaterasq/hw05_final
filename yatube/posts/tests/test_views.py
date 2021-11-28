import shutil
import tempfile
# from django.http import response

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, User, Comment, Follow
from yatube.settings import POSTS_ON_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

INDEX_URL = reverse('posts:index')
USERNAME = 'Ivan'
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
SLUG = 'test-slug'
SLUG2 = 'test-slug2'
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
GROUP_LIST2_URL = reverse('posts:group_list', args=[SLUG2])
# 6 спринт
POST_IMAGE_TEST = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
UPLOADED_IMAGE = SimpleUploadedFile(
    name='small.gif',
    content=POST_IMAGE_TEST,
    content_type='image/gif'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Ivan')
        cls.user = User.objects.create_user(username='StasBasov')
        # Создадим 2 группы
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG,
            description='Тестовый текст',
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок2',
            slug=SLUG2,
            description='Тестовый текст2',
        )
        # Создадим пост
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
            image=UPLOADED_IMAGE
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            args=[cls.post.id]
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем авторизованный клиент, автора поста
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_pages_show_correct_context(self):
        """Страницы posts:index, posts:group_list, posts:profile, posts:post_detail
           содержат ожидаемый контекст"""
        pages = [
            [INDEX_URL, 'page_obj'],
            [GROUP_LIST_URL, 'page_obj'],
            [PROFILE_URL, 'page_obj'],
            [self.POST_DETAIL_URL, 'post'],
        ]
        for url, item in pages:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                if item == 'page_obj':
                    self.assertEqual(len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.pk, self.post.id)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)

    def test_page_index_cache(self):
        ''' Тест, проверяющий работу кэша '''
        cache_post = Post.objects.create(
            text='Тест кэша',
            author=self.author,
            group=self.group,
        )
        response = self.guest_client.get(INDEX_URL)
        self.assertEqual(response.context['page_obj'][0].text, cache_post.text)
        cache_post.delete()
        self.assertEqual(response.context['page_obj'][0].text, cache_post.text)
        # CACHES.clear()
        cache.clear()
        response = self.guest_client.get(INDEX_URL)
        self.assertNotEqual(
            response.context['page_obj'][0].text,
            cache_post.text
        )

    def test_group_pages_show_correct_constant_context(self):
        '''На страницу группы выводится объявленная группа'''
        response = self.guest_client.get(GROUP_LIST_URL)
        group = response.context['group']
        self.assertEqual(group, self.group)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.slug, self.group.slug)

    def test_profile_pages_show_correct_constant_context(self):
        '''На страницу автора выводится объявленный автор'''
        response = self.guest_client.get(PROFILE_URL)
        self.assertEqual(response.context['author'], self.post.author)

    def test_pages_not_show_incorrect_context(self):
        '''На страницу второй группы не передается пост из первой'''
        response = self.guest_client.get(GROUP_LIST2_URL)
        self.assertNotIn(self.post.id, response.context['page_obj'])

    def test_comments_authorized_client(self):
        '''Комментировать запись может авторизованный пользователь,
        после отправки комментария он появляется на странице записи'''
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        created_comments = response.context['post'].comments.all()
        self.assertEqual(len(created_comments), 1)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(response, self.POST_DETAIL_URL,)
        comment = self.post.comments.get()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)

    def test_guest_client_cant_comments(self):
        ''' Неавторизованный пользователь не может оставить комментарий '''
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_authorized_client_following_and_unfollowing_author(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow', args=['Ivan'])
        )
        self.assertEqual(
            Follow.objects.filter(user=self.user).count(),
            1
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', args=['Ivan'])
        )
        self.assertEqual(
            Follow.objects.filter(user=self.user).count(),
            0
        )

    def test_posts_with_following_on_follow_index(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow', args=['Ivan'])
        )
        response = self.authorized_client.get(reverse(
            'posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 1)
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.pk, self.post.id)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.image, self.post.image)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', args=['Ivan'])
        )
        response = self.authorized_client.get(reverse(
            'posts:follow_index')
        )
        self.assertNotIn(self.post.id, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    '''Проверка пагинатора на страницах: posts:index,
       posts:group_list, posts:profile.'''
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Ivan')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.post = Post.objects.bulk_create([
            Post(text='Тестовый текст',
                 author=cls.author,
                 group=cls.group
                 ) for _ in range(POSTS_ON_PAGE + 3)
        ])
        cls.urls = [
            INDEX_URL,
            GROUP_LIST_URL,
            PROFILE_URL,
        ]

    def test_first_page_contains_records(self):
        """Вывод заданного числа постов на первую страницую."""
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(len(
                    response.context['page_obj']),
                    POSTS_ON_PAGE
                )

    def test_second_page_contains_last_records(self):
        """Вывод оставшихся постов на вторую страницую."""
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
