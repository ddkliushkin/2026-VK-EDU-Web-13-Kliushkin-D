from django.contrib import admin
from .models import Tag, Question, Answer, QuestionLike, AnswerLike


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ('author', 'text', 'is_correct', 'rating')
    raw_id_fields = ('author',)
    show_change_link = True


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'rating', 'created_at')
    search_fields = ('title', 'text', 'author__username')
    list_filter = ('created_at',)
    raw_id_fields = ('author', 'tags')
    list_select_related = ('author',)
    inlines = (AnswerInline,)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_correct', 'rating', 'created_at')
    search_fields = ('text', 'author__username', 'question__title')
    list_filter = ('is_correct', 'created_at')
    raw_id_fields = ('question', 'author')
    list_select_related = ('question', 'author')


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'question', 'value')
    search_fields = ('user__username', 'question__title')
    list_filter = ('value',)
    raw_id_fields = ('user', 'question')
    list_select_related = ('user', 'question')


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'answer', 'value')
    search_fields = ('user__username', 'answer__text')
    list_filter = ('value',)
    raw_id_fields = ('user', 'answer')
    list_select_related = ('user', 'answer')