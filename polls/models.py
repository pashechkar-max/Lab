import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver



class UserProfile(models.Model):

    # профиля пользователя
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(
        upload_to='avatars/',
        verbose_name='Аватар',
        default='avatars/ez.jpg'  # Файл по умолчанию
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name='О себе')

    def __str__(self):
        return f'Profile of {self.user.username}'

    def save(self, *args, **kwargs):
        # Можно добавить обработку изображения при сохранении
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):

    # профиль пользователя при

    if created:
        # аватар по
        default_avatar = 'media/avatars/ez.jpg'
        UserProfile.objects.create(user=instance, avatar=default_avatar)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль пользователя при сохранении пользователя"""
    instance.profile.save()


class Question(models.Model):
    """Модель вопроса для опроса"""
    question_text = models.CharField(max_length=200)
    short_description = models.CharField(max_length=300, default='')
    full_description = models.TextField(default='')
    pub_date = models.DateTimeField('date published', default=timezone.now)
    expiration_date = models.DateTimeField('expiration date', default=timezone.now() + datetime.timedelta(days=7))
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    image = models.CharField(max_length=200, blank=True, null=True)  # Временное решение
    image = models.ImageField(upload_to='question_images/', blank=True, null=True, verbose_name='Изображение')

    def is_active(self):
        """Проверяет, активен ли еще вопрос для голосования"""
        now = timezone.now()
        return self.pub_date <= now <= self.expiration_date

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

    def __str__(self):
        return self.question_text

    class Meta:
        ordering = ['-pub_date']


class Choice(models.Model):
    """Модель варианта ответа"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


class Vote(models.Model):
    """Модель для отслеживания голосов пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'question']

    def __str__(self):
        return f'{self.user.username} voted for {self.choice.choice_text}'


class MicroblogPost(models.Model):
    """Модель поста микроблога"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=1000, verbose_name='Текст поста')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Пост микроблога'
        verbose_name_plural = 'Посты микроблога'

    def __str__(self):
        return f'Пост от {self.author.username}'

    def get_comment_count(self):
        return self.comments.count()


class PostLike(models.Model):
    """Модель лайка поста"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(MicroblogPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        verbose_name = 'Лайк поста'
        verbose_name_plural = 'Лайки постов'

    def __str__(self):
        return f'{self.user.username} лайкнул пост #{self.post.id}'


class PostComment(models.Model):
    """Модель комментария к посту"""
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(MicroblogPost, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=500, verbose_name='Текст комментария')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'Комментарий от {self.author.username}'