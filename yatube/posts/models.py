from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
POST_STR = 15


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('Текст поста', help_text='Введите текст поста')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:POST_STR]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField('Комментарий', help_text='Оставьте комментарий')
    created = models.DateTimeField('Дата и время публикации',
                                   auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User,
                             verbose_name='Подписчик',
                             related_name='follower',
                             on_delete=models.CASCADE)
    author = models.ForeignKey(User, verbose_name='Автор',
                               related_name='following',
                               on_delete=models.CASCADE)
