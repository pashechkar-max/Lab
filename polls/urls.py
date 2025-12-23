from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


app_name = 'polls'
urlpatterns = [
    #основные маршруты
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    path('<int:question_id>/vote/', views.vote, name='vote'),

    #для пользователей
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='polls/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='polls/logout.html', next_page='polls:index'), name='logout'),

    #профиля
    path('profile/', views.profile, name='profile'),
    path('profile/delete/', views.delete_profile, name='delete_profile'),
    path('users/<str:username>/', views.user_profile, name='user_profile'),
    path("users/<str:username>/edit/",views.edit_profile,name="edit_profile"),

    # Вопросы
    path('create/', views.create_question, name='create_question'),

    path('microblog/', views.microblog_feed, name='microblog_feed'),
    path('microblog/create/', views.create_post, name='create_post'),
    path('microblog/post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('microblog/post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('microblog/post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('microblog/post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('microblog/comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('microblog/comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),

    path('microblog/', views.microblog_feed, name='microblog')
]
