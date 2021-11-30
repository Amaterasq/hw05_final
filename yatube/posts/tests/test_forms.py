import shutil
import tempfile
from django.shortcuts import get_object_or_404
from http import HTTPStatus

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, User, Group, Follow, Comment

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
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
        post_image_edit = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        UPLOADED_IMAGE2 = SimpleUploadedFile(
            name='small.gif',
            content=post_image_edit,
            content_type='image/gif'
        )
        edit_group = Group.objects.create(
            title='Группа для редактирования поста',
            slug='test-slug-edit',
            description='Описание'
        )
        edit_data = {
            'text': 'Отредактированный текст',
            'group': edit_group.id,
            'image': UPLOADED_IMAGE2,
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
        self.assertTrue(edit_post.image)

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
        self.assertEqual(comment.post, self.post)

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
        self.assertNotIn(
            self.post,
            Comment.objects.filter(text__exact=form_data['text'])
        )
