from django.contrib import admin
from .models import Question, Choice, Vote, UserProfile


class ChoiceInLine(admin.TabularInline):
    model = Choice
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'pub_date', 'expiration_date', 'is_active')
    list_filter = ['pub_date', 'expiration_date']
    search_fields = ['question_text']
    inlines = [ChoiceInLine]


class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'choice', 'voted_at')
    list_filter = ['question', 'voted_at']


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar')


admin.site.register(Question, QuestionAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

# Добавить в admin.py
from .models import MicroblogPost, PostLike, PostComment


class PostCommentInline(admin.TabularInline):
    model = PostComment
    extra = 1


class MicroblogPostAdmin(admin.ModelAdmin):
    list_display = ('author', 'content_preview', 'created_at', 'likes_count')
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username']
    inlines = [PostCommentInline]

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Содержание'


class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'content_preview', 'post', 'created_at')
    list_filter = ['created_at', 'author']
    search_fields = ['content', 'author__username']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Комментарий'


# Зарегистрировать новые модели
admin.site.register(MicroblogPost, MicroblogPostAdmin)
admin.site.register(PostLike)
admin.site.register(PostComment, PostCommentAdmin)