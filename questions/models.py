from django.db import models
from django.db.models import Count, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.urls import reverse


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tag', kwargs={'tag_name': self.name})


class QuestionManager(models.Manager):
    def with_details(self):
        answers_count_sq = (
            Answer.objects.filter(question=OuterRef('pk'))
            .values('question')
            .annotate(cnt=Count('id'))
            .values('cnt')
        )
        return (
            self.get_queryset()
            .select_related('author', 'author__profile')
            .prefetch_related('tags')
            .annotate(
                answers_count=Coalesce(
                    Subquery(answers_count_sq, output_field=IntegerField()),
                    0,
                )
            )
        )

    def new(self):
        return self.with_details().order_by('-created_at', '-id')

    def hot(self):
        return self.with_details().order_by('-rating', '-created_at')

    def by_tag(self, tag):
        return self.with_details().filter(tags=tag).order_by('-created_at', '-id')


class Question(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст вопроса')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='questions',
        verbose_name='Теги',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания',
    )
    rating = models.IntegerField(
        default=0,
        db_index=True,
        verbose_name='Рейтинг',
    )

    objects = QuestionManager()

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('question', kwargs={'question_id': self.pk})


class AnswerManager(models.Manager):
    def for_question(self, question):
        return (
            self.get_queryset()
            .filter(question=question)
            .select_related('author', 'author__profile')
            .order_by('-is_correct', '-rating', 'created_at')
        )


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Вопрос',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Автор',
    )
    text = models.TextField(verbose_name='Текст ответа')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания',
    )
    rating = models.IntegerField(default=0, verbose_name='Рейтинг')

    objects = AnswerManager()

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        ordering = ['-is_correct', '-rating', 'created_at']

    def __str__(self):
        return f'Ответ #{self.pk} на вопрос #{self.question_id}'


class QuestionLike(models.Model):
    LIKE = 1
    DISLIKE = -1
    VALUE_CHOICES = (
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='question_likes',
        verbose_name='Пользователь',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Вопрос',
    )
    value = models.SmallIntegerField(choices=VALUE_CHOICES, default=LIKE, verbose_name='Оценка')

    class Meta:
        verbose_name = 'Оценка вопроса'
        verbose_name_plural = 'Оценки вопросов'
        unique_together = ('user', 'question')

    def __str__(self):
        return f'{self.user.username} -> Вопрос #{self.question_id} ({self.value})'


class AnswerLike(models.Model):
    LIKE = 1
    DISLIKE = -1
    VALUE_CHOICES = (
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answer_likes',
        verbose_name='Пользователь',
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Ответ',
    )
    value = models.SmallIntegerField(choices=VALUE_CHOICES, default=LIKE, verbose_name='Оценка')

    class Meta:
        verbose_name = 'Оценка ответа'
        verbose_name_plural = 'Оценки ответов'
        unique_together = ('user', 'answer')

    def __str__(self):
        return f'{self.user.username} -> Ответ #{self.answer_id} ({self.value})'