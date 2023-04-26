from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from mixer.backend.django import mixer

from ..models import Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username="AlexPushkin")
        cls.group = mixer.blend('posts.Group')
        cls.post = Post.objects.create(author=cls.user, text='Тестовый пост',)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_common_urls(self):
        """Проверка общедоступных urls"""
        common_urls = ['/', f'/group/{self.group.slug}/',
                       f'/profile/{self.user.username}/',
                       f'/posts/{self.post.pk}/']
        for url in common_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                error_message = f' доступ к {url} работает неправильно'
                self.assertEqual(response.status_code,
                                 HTTPStatus.OK, error_message)

    def test_not_used_urls(self):
        """Проверка несуществующих страниц"""
        response = self.client.get('/unexistring_page/')
        error_message = '''Переход на несуществующую
        страницу осуществлен неправильно'''
        self.assertEqual(response.status_code,
                         HTTPStatus.NOT_FOUND, error_message)

    def test_authorized_urls(self):
        """Проверка страницы, доступной только для авториз. пользователей"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_url(self):
        """Проверка страницы, доступной только автору поста"""
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_templates_urls(self):
        """Проверка шаблонов"""
        templates_to_urls = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        cache.clear()
        for url, template in templates_to_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
