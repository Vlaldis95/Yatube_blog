from django.test import TestCase

from ..models import Group, Post, User

POST_LENGTH = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_post_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        error_message = 'У модели Post неправильно работает метод __str__'
        self.assertEqual(str(self.post), self.post.text[:POST_LENGTH],
                         error_message)

    def test_verbose_name(self):
        """Проверяем,что у модели Post правильно указан атрибут verbose_name"""
        field_verboses = {'text': 'Текст поста',
                          'pub_date': 'Дата публикации',
                          'author': 'Автор',
                          'group': 'Группа',
                          }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                error_message = f'''У модели Post неправильно указано
                verbose_name для поля {field}'''
                self.assertEqual(self.post._meta.get_field(field).verbose_name,
                                 expected_value, error_message)

    def test_help_text(self):
        """Проверяем,что у модели Post правильно указан атрибут help_text"""
        field_help_text = {'text': 'Введите текст поста',
                           'group': 'Группа, к которой будет относиться пост'}
        for field, expected_value in field_help_text.items():
            with self.subTest(field=field):
                error_message = f'''У модели Post неправильно указан
                help_text для поля {field}'''
                self.assertEqual(self.post._meta.get_field(field).help_text,
                                 expected_value, error_message)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        error_message = 'У модели Group неправильно работает метод __str__'
        self.assertEqual(str(self.group), self.group.title, error_message)
