import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='IvanMakarov')
        cls.user2 = User.objects.create_user(username='AlexPushkin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cls.group.delete()
        cls.post.delete()
        cls.user.delete()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(PostPagesTest.user)
        cache.clear()

    def test_pages_on_templates(self):
        """Проверка соответсвия шаблонов страницам"""
        pages_and_templates = {reverse('posts:index'): 'posts/index.html',
                               reverse('posts:group_list',
                                       kwargs={'slug': self.group.slug}):
                               'posts/group_list.html',
                               reverse('posts:profile',
                                       kwargs={'username':
                                               self.user.username}):
                               'posts/profile.html',
                               reverse('posts:post_detail',
                                       kwargs={'post_id': self.post.id}):
                               'posts/post_detail.html',
                               reverse('posts:post_edit',
                                       kwargs={'post_id': self.post.id}):
                               'posts/create_post.html',
                               reverse('posts:post_create'):
                               'posts/create_post.html',
                               '/unexistring_page/':
                               'core/404.html'}
        for reverse_name, template in pages_and_templates.items():
            with self.subTest(reverse_name=reverse_name):
                error_message = f'''Неправильный шаблон
                у страницы {reverse_name}'''
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template, error_message)

    def test_main_page_context(self):
        """Шаблон главной страницы сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:index'))
        post_image = Post.objects.first().image
        self.assertEqual(list(response.context['page_obj']),
                         list(Post.objects.all()[:10]))
        self.assertEqual(post_image, 'posts/small.gif',
                         'В контексте шаблона главной страницы нет картинки')

    def test_group_page_context(self):
        """Шаблон страницы группы сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        post_image = Post.objects.first().image
        self.assertEqual(list(response.context['page_obj']),
                         list(Post.objects.filter
                              (group_id=self.group.id)[:10]))
        self.assertEqual(post_image, 'posts/small.gif',
                         'В контексте шаблона страницы группы нет картинки')

    def test_user_page_context(self):
        """Шаблон страницы пользователя сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        post_image = Post.objects.first().image
        self.assertEqual(list(response.context['page_obj']),
                         list(Post.objects.filter
                              (author_id=self.user.id)[:10]))
        self.assertEqual(post_image, 'posts/small.gif',
                         'В контексте шаблона профиля автора нет картинки')

    def test_post_id_page_context(self):
        """Шаблон страницы поста сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_image = Post.objects.get(id=self.post.id).image
        self.assertEqual(response.context['post'],
                         Post.objects.get(id=self.post.id))
        self.assertEqual(post_image, 'posts/small.gif',
                         'В контексте шаблона поста нет картинки')

    def test_post_create_page_context(self):
        """Шаблон страницы создания поста
        сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_context(self):
        """Шаблон страницы редактирования поста
        сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField}
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_correct_create_page_redirect(self):
        """Страница создания поста правильно
          перенаправляет на главную страницу"""
        self.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_group2')
        self.authorized_client2.force_login(PostPagesTest.user2)
        self.post = Post.objects.create(
            text='Тестовый пост от другого автора',
            author=self.user2,
            group=self.group2)
        check_data = {reverse('posts:index'): 'поста нет на главной странице',
                      reverse('posts:group_list',
                      kwargs={'slug': self.group2.slug}):
                      'поста нет на странице группы',
                      reverse('posts:profile',
                              kwargs={'username': self.user2.username}):
                      'поста нет на странице пользователя'}
        for page, message in check_data.items():
            with self.subTest(page=page):
                response = self.authorized_client2.get(page)
                post_in_page = response.context['page_obj']
                self.assertIn(self.post, post_in_page, message)
        response_an_gr = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        post_in_page2 = response_an_gr.context['page_obj']
        self.assertNotIn(self.post, post_in_page2, 'пост есть в другой группе')


class PostPaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='VasilyPetrov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts_list = Post.objects.bulk_create(
            [Post(author=cls.user, text='Тестовый пост',
                  group=cls.group) for _ in range(13)])

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_paginator(self):
        """ Проверка: количество постов на первой странице равно 10"""
        paginate_pages = [reverse('posts:index'),
                          reverse('posts:group_list',
                                  kwargs={'slug': self.group.slug}),
                          reverse('posts:profile',
                                  kwargs={'username': self.user.username})]
        for url in paginate_pages:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_paginator(self):
        """ Проверка: количество постов на второй странице равно 3"""
        paginate_pages = [reverse('posts:index'),
                          reverse('posts:group_list',
                                  kwargs={'slug': self.group.slug}),
                          reverse('posts:profile',
                                  kwargs={'username': self.user.username})]
        for url in paginate_pages:
            with self.subTest(url=url):
                response = self.authorized_client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='SergeiIvanov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_comment_for_guest(self):
        '''Неавторизованный пользователь не может оставить комментарий'''
        response = self.client.get(reverse('posts:add_comment',
                                           kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.status_code,
                         HTTPStatus.FOUND,
                         '''Неавторизованный пользователь
                         не может оставлять комментарий''')

    def test_add_comment_for_auth_user(self):
        '''Авторизованный пользователь может оставить комментарий'''
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.status_code,
                         HTTPStatus.OK,
                         '''Авторизованный пользователь
                         должен иметь возможность оставить комментарий''')

    def test_post_id_page_context(self):
        """В шаблоне страницы поста есть комментарии"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_comments = Comment.objects.filter(post=self.post.id)
        self.assertEqual(list(post_comments),
                         list(response.context['comments']),
                         'В контексте шаблона нет комментариев')


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='AlexPushkin')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='test_group',
            slug='test-slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='test_post',
            group=cls.group,
            author=cls.author
        )

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts_before_cache = response.content
        created_post = Post.objects.get(
            text='test_post',
            group=self.group,
            author=self.author,
        )
        created_post.delete()
        response_old = self.authorized_client.get(
            reverse('posts:index')
        )
        posts_after_cache = response_old.content
        self.assertEqual(
            posts_after_cache,
            posts_before_cache,
            'Не возвращает кэшированную страницу.'
        )
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(posts_after_cache,
                            new_posts, 'Сброс кэша не происходит.')


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='IvanSergeev')
        cls.user2 = User.objects.create_user(username='AlexVasnetsov')
        cls.user3 = User.objects.create_user(username='MikeLermontov')
        cls.post = Post.objects.create(text='Подписка', author=cls.user2)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client3 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)
        self.authorized_client3.force_login(self.user3)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.user2.delete()
        cls.user3.delete()
        cls.post.delete()

    def test_follow_user(self):
        """Проверка подписки и отписки от автора"""
        follows_count = Follow.objects.all()
        follows_count.delete()
        follows_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user2.username}))
        self.assertEqual(Follow.objects.count(),
                         follows_count + 1, 'Подписка не создается')
        count_after_follow = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user2.username}))
        self.assertNotEqual(count_after_follow, Follow.objects.count(),
                            'Подписка не удаляется')

    def author_post_in_follow_index(self):
        """Проверка наличия поста автора на странице подписчика"""
        Follow.objects.create(user=self.user, author=self.user2)
        response = self.authorized_client.get('posts:follow_index')
        another_response = self.authorized_client3.get('posts:follow_index')
        post_in_page_new = another_response.context['page_obj'][0]
        post_in_page = response.context['page_obj'][0]
        self.assertEqual(self.post,
                         post_in_page, 'Поста нет на странице подписчика')
        self.assertNotEqual(self.post,
                            post_in_page_new,
                            'Пост есть на странице неподписчика')
