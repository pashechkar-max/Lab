from django import forms
from .models import UserProfile, Question, MicroblogPost, PostComment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# forms.py
class UserProfileForm(forms.ModelForm):
    # редактирования профиля пользователя
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'  # Принимать только изображения
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
        }
        labels = {
            'avatar': 'Аватар',
            'bio': 'О себе',
        }
        help_texts = {
            'avatar': 'Загрузите изображение для аватара (обязательно)',
            'bio': 'Необязательное поле',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['avatar'].required = True

class QuestionForm(forms.ModelForm):
    #создания вопроса
    class Meta:
        model = Question
        fields = ['question_text', 'short_description', 'full_description', 'expiration_date', 'image']
        labels = {
            'question_text': 'Текст вопроса',
            'short_description': 'Краткое описание',
            'full_description': 'Полное описание',
            'expiration_date': 'Дата окончания',
            'image': 'Изображение',
        }
        widgets = {
            'expiration_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            'short_description': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Краткое описание вопроса (макс. 300 символов)'
            }),
            'full_description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Полное описание вопроса'
            }),
            'question_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите текст вопроса'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }

    # Варианты ответов
    choice1 = forms.CharField(
        max_length=200,
        label='Вариант ответа 1',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите вариант ответа',
            'required': True
        })
    )
    choice2 = forms.CharField(
        max_length=200,
        label='Вариант ответа 2',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите вариант ответа',
            'required': True
        })
    )
    choice3 = forms.CharField(
        max_length=200,
        label='Вариант ответа 3',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите вариант ответа (необязательно)'
        })
    )
    choice4 = forms.CharField(
        max_length=200,
        label='Вариант ответа 4',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите вариант ответа (необязательно)'
        })
    )


class CustomUserCreationForm(UserCreationForm):
    #форма регистрации с для аватара
    avatar_url = forms.URLField(
        label='Аватар (URL)',
        required=True,
        help_text='Введите URL изображения для вашего аватара',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://example.com/avatar.jpg'
        })
    )
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'avatar_url']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            # Профиль
            UserProfile.objects.create(
                user=user,
                avatar=self.cleaned_data['avatar_url']
            )

        return user

# Добавить в forms.py

class MicroblogPostForm(forms.ModelForm):
    """Форма для создания и редактирования поста"""
    class Meta:
        model = MicroblogPost
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Что у вас нового?',
                'maxlength': 1000
            }),
        }
        labels = {
            'content': 'Текст поста'
        }


class PostCommentForm(forms.ModelForm):
    """Форма для комментариев"""
    class Meta:
        model = PostComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Напишите комментарий...',
                'maxlength': 500
            }),
        }
        labels = {
            'content': 'Комментарий'
        }