import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_DIR = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_DIR)
class PostCreateFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='SergeyEsenin')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(author=self.user,
                                        text='Новый пост')

    def tearDown(self):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        self.post.delete()

    def test_post_create_form(self):
        """Валидная форма создает запись"""
        all_posts = Post.objects.all()
        all_posts.delete()
        posts_count = Post.objects.count()
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост',
            'image': uploaded}
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse("posts:profile",
                              kwargs={"username": self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(text='Тестовый пост',
                                author=self.user.id,
                                image=self.post.image).exists()
        )

    def test_post_edit_form(self):
        """Валидная форма редактирует запись"""
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
        )
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug7',
            description='Тестовое описание',
        )
        posts_count = Post.objects.count()
        small_gif2 = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                      b'\x01\x00\x80\x00\x00\x00\x00\x00'
                      b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                      b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                      b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                      b'\x0A\x00\x3B')
        uploaded1 = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif2,
            content_type='image/gif')
        form_data = {
            'group': self.group.id,
            'text': 'Изменяем текст',
            'image': uploaded1}
        response = self.authorized_client.post(
            reverse("posts:post_edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(text='Изменяем текст',
                                group=self.group.id,
                                author=self.user.id,
                                image='posts/small2.gif').exists())


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='IvanMakarov')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.user.delete()
        cls.post.delete()

    def test_comment_create(self):
        "Форма сохраняет комментарий в Базу данных"
        all_comments = Comment.objects.filter(post=self.post.pk)
        all_comments.delete()
        comments_count = Comment.objects.filter(post=self.post.pk).count()
        form_data = {'text': 'test_comment'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        comments = Comment.objects.filter(post=self.post.pk)
        self.assertEqual(comments.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=form_data['text']).exists())
