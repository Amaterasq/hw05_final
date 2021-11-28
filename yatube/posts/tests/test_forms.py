import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, User, Group

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

POST_CREATE_URL = reverse('posts:post_create')
USERNAME = 'StasBasov'
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
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
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Ivan')
        cls.user = User.objects.create_user(username=USERNAME)
        # Создадим группу
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        # Создадим пост
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
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

    def test_create_post(self):
        """Создание записи через форму"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': UPLOADED_IMAGE,
        }
        existing_posts_ids = set(Post.objects.all().values_list(
            'id', flat=True)
        )

        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        created_posts = Post.objects.exclude(id__in=existing_posts_ids)
        self.assertEqual(len(created_posts), 1)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, PROFILE_URL,)
        created_post = created_posts.get()
        self.assertEqual(created_post.text, form_data['text'])
        self.assertEqual(created_post.author, self.user)
        self.assertEqual(created_post.group.id, form_data['group'])
        self.assertTrue(created_post.image)

    def test_edit_post(self):
        """Редактирование записи"""
        edit_group = Group.objects.create(
            title='Группа для редактирования поста',
            slug='test-slug-edit',
            description='Описание'
        )
        edit_data = {
            'text': 'Отредактированный текст',
            'group': edit_group.id,
        }
        response = self.authorized_author.post(
            self.POST_EDIT_URL,
            data=edit_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        edit_post = response.context['post']
        self.assertEqual(edit_post.text, edit_data['text'])
        self.assertEqual(edit_post.author, self.post.author)
        self.assertEqual(edit_post.group.id, edit_data['group'])

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(POST_CREATE_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
