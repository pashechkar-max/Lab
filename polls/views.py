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