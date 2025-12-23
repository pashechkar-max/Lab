from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Question, Choice, Vote, UserProfile
from .forms import CustomUserCreationForm, UserProfileForm, QuestionForm
from django.contrib.auth.models import User


#регистрация пользователя
def register(request):
    # регистрация нового пользователя
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                # Вход пользователя
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Регистрация прошла успешно!')
                    return redirect('polls:index')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'polls/register.html', {'form': form})

# Профиль пользователя
@login_required
def profile(request):
    """Просмотр и редактирование профиля пользователя"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('polls:profile')
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'polls/profile.html', {'form': form, 'profile': user_profile})

@login_required
def delete_profile(request):
    if request.method == 'POST':
        # Удаление пользователя
        request.user.delete()
        messages.success(request, 'Ваш профиль был успешно удален.')
        return redirect('polls:index')
    return render(request, 'polls/delete_profile_confirm.html')


# вопрос
@login_required
def create_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)  # Важно: request.FILES для загрузки файлов
        if form.is_valid():
            question = form.save(commit=False)
            question.author = request.user
            question.save()

            #варианты ответов
            choices = [
                form.cleaned_data.get('choice1'),
                form.cleaned_data.get('choice2'),
                form.cleaned_data.get('choice3'),
                form.cleaned_data.get('choice4'),
            ]

            for choice_text in choices:
                if choice_text:  # создаем непустые варианты
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_text
                    )

            messages.success(request, 'Вопрос успешно создан!')
            return redirect('polls:detail', pk=question.pk)
    else:
        form = QuestionForm()

    return render(request, 'polls/create_question.html', {'form': form})

# Главная страница

class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):

        now = timezone.now()
        if self.request.user.is_superuser:
            return Question.objects.all()
        return Question.objects.filter(
            expiration_date__gt=now,
            pub_date__lte=now
        ).order_by('-pub_date')


# Детали вопроса
class DetailView(LoginRequiredMixin, generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Question.objects.all()
        now = timezone.now()
        return Question.objects.filter(
            expiration_date__gt=now,
            pub_date__lte=now
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()

        # голосовал ли уже пользователь
        has_voted = Vote.objects.filter(
            user=self.request.user,
            question=question
        ).exists()

        context['has_voted'] = has_voted

        if has_voted:
            # Если уже голосовал, показываем результаты
            user_vote = Vote.objects.get(user=self.request.user, question=question)
            context['user_choice'] = user_vote.choice

        return context


# Результаты
class ResultsView(LoginRequiredMixin, generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        question = self.get_object()


        votes = Vote.objects.filter(question=question)
        total_votes = votes.count()

        choices_with_percentage = []
        for choice in question.choices.all():
            if total_votes > 0:
                percentage = (choice.votes / total_votes) * 100
            else:
                percentage = 0

            choices_with_percentage.append({
                'choice': choice,
                'percentage': round(percentage, 1),
                'votes': choice.votes
            })

        context['choices_with_percentage'] = choices_with_percentage
        context['total_votes'] = total_votes

        return context


# Голосование
@login_required
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)

    # активен ли еще вопрос
    if not question.is_active() and not request.user.is_superuser:
        messages.error(request, 'Голосование по этому вопросу завершено.')
        return redirect('polls:detail', pk=question.id)

    #голосовал ли уже пользователь
    if Vote.objects.filter(user=request.user, question=question).exists():
        messages.error(request, 'Вы уже голосовали по этому вопросу.')
        return redirect('polls:detail', pk=question.id)

    try:
        selected_choice = question.choices.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        messages.error(request, 'Вы не сделали выбор.')
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': 'Вы не сделали выбор'
        })

    # счетчик голосов
    selected_choice.votes += 1
    selected_choice.save()

    # голос пользователя
    Vote.objects.create(
        user=request.user,
        question=question,
        choice=selected_choice
    )

    messages.success(request, 'Ваш голос учтен!')
    return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


# Добавить импорты
from .models import MicroblogPost, PostLike, PostComment
from .forms import MicroblogPostForm, PostCommentForm
from django.core.paginator import Paginator


# Добавить представления для микроблогов

@login_required
def create_post(request):
    """Создание нового поста"""
    if request.method == 'POST':
        form = MicroblogPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Пост опубликован!')
            return redirect('polls:microblog_feed')
    else:
        form = MicroblogPostForm()

    return render(request, 'polls/create_post.html', {'form': form})


def microblog_feed(request):
    """Лента постов (главная страница микроблогов)"""
    posts_list = MicroblogPost.objects.all().select_related('author')
    paginator = Paginator(posts_list, 10)  # 10 постов на странице

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    comment_form = PostCommentForm()

    return render(request, 'polls/microblog_feed.html', {
        'page_obj': page_obj,
        'comment_form': comment_form,
    })


@login_required
def edit_post(request, post_id):
    """Редактирование поста"""
    post = get_object_or_404(MicroblogPost, id=post_id, author=request.user)

    if request.method == 'POST':
        form = MicroblogPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пост обновлен!')
            return redirect('polls:user_profile', username=request.user.username)
    else:
        form = MicroblogPostForm(instance=post)

    return render(request, 'polls/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, post_id):
    """Удаление поста"""
    post = get_object_or_404(MicroblogPost, id=post_id, author=request.user)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Пост удален!')
        return redirect('polls:user_profile', username=request.user.username)

    return render(request, 'polls/delete_post_confirm.html', {'post': post})


@login_required
def like_post(request, post_id):
    """Лайк/анлайк поста"""
    post = get_object_or_404(MicroblogPost, id=post_id)

    # Проверяем, лайкал ли уже пользователь этот пост
    like_exists = PostLike.objects.filter(user=request.user, post=post).exists()

    if like_exists:
        # Убираем лайк
        PostLike.objects.filter(user=request.user, post=post).delete()
        post.likes_count -= 1
        liked = False
    else:
        # Ставим лайк
        PostLike.objects.create(user=request.user, post=post)
        post.likes_count += 1
        liked = True

    post.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX запрос
        return JsonResponse({
            'liked': liked,
            'likes_count': post.likes_count
        })

    return redirect(request.META.get('HTTP_REFERER', 'polls:microblog_feed'))


@login_required
def add_comment(request, post_id):
    """Добавление комментария"""
    post = get_object_or_404(MicroblogPost, id=post_id)

    if request.method == 'POST':
        form = PostCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            messages.success(request, 'Комментарий добавлен!')

    return redirect(request.META.get('HTTP_REFERER', 'polls:microblog_feed'))


@login_required
def edit_comment(request, comment_id):
    """Редактирование комментария"""
    comment = get_object_or_404(PostComment, id=comment_id, author=request.user)

    if request.method == 'POST':
        form = PostCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Комментарий обновлен!')
            return redirect('polls:microblog_feed')
    else:
        form = PostCommentForm(instance=comment)

    return render(request, 'polls/edit_comment.html', {'form': form, 'comment': comment})


@login_required
def delete_comment(request, comment_id):
    """Удаление комментария"""
    comment = get_object_or_404(PostComment, id=comment_id, author=request.user)

    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Комментарий удален!')

    return redirect(request.META.get('HTTP_REFERER', 'polls:microblog_feed'))


def user_profile(request, username):
    """Профиль пользователя с его постами"""
    user = get_object_or_404(User, username=username)
    user_profile_obj = user.profile

    posts_list = MicroblogPost.objects.filter(author=user)
    paginator = Paginator(posts_list, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile_user': user,
        'user_profile': user_profile_obj,
        'page_obj': page_obj,
    }

    return render(request, 'polls/user_profile.html', context)


# Обновить существующую функцию profile для редактирования своего профиля
@login_required
def edit_profile(request):
    """Редактирование профиля пользователя"""
    user_profile_obj = request.user.profile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен!')
            return redirect('polls:user_profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=user_profile_obj)

    return render(request, 'polls/edit_profile.html', {'form': form})

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def edit_profile(request, username):
    if request.user.username != username:
        return redirect("polls:user_profile", username=username)

    if request.method == "POST":
        # позже добавим форму
        pass

    return render(request, "polls/edit_profile.html", {
        "profile_user": request.user
    })