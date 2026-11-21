from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from .models import Question, Answer, Tag, QuestionLike, AnswerLike


class QuestionForm(forms.ModelForm):
    tags_input = forms.CharField(
        max_length=80,
        label='Теги',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: поиск_ошибки, теория, оффтоп',
        }),
    )

    class Meta:
        model = Question
        fields = ('title', 'text')
        labels = {
            'title': 'Заголовок',
            'text': 'Текст вопроса',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 120,
                'placeholder': 'Сформулируйте суть вопроса в одном предложении',
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 7,
                'maxlength': 10000,
                'placeholder': 'Опишите проблему подробно...',
            }),
        }

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 5:
            raise ValidationError('Заголовок должен содержать минимум 5 символов.')
        if len(title) > 120:
            raise ValidationError('Максимальная длина заголовка — 120 символов.')
        return title

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if len(text) < 30:
            raise ValidationError('Текст вопроса должен содержать минимум 30 символов.')
        return text

    def clean_tags_input(self):
        raw = self.cleaned_data['tags_input']
        parsed = []
        for part in raw.split(','):
            name = part.strip().lstrip('#').strip().lower()
            if name and name not in parsed:
                if len(name) > 20:
                    raise ValidationError(f'Тег «{name}» длиннее 20 символов.')
                parsed.append(name)

        if not (1 <= len(parsed) <= 3):
            raise ValidationError('Укажите от 1 до 3 уникальных тегов через запятую.')
        return parsed

    def save(self, author, commit=True):
        question = super().save(commit=False)
        question.author = author
        if commit:
            question.save()
            tag_objects = [Tag.objects.get_or_create(name=name)[0] for name in self.cleaned_data['tags_input']]
            question.tags.set(tag_objects)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('text',)
        labels = {'text': 'Текст ответа'}
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'maxlength': 5000,
                'placeholder': 'Напишите подробный и развернутый ответ на вопрос...',
            }),
        }

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if len(text) < 5:
            raise ValidationError('Ответ слишком короткий (минимум 5 символов).')
        return text

    def save(self, question, author, commit=True):
        answer = super().save(commit=False)
        answer.question = question
        answer.author = author
        if commit:
            answer.save()
        return answer


class VoteForm(forms.Form):
    VOTE_TYPES = (
        ('like', 'Лайк'),
        ('dislike', 'Дизлайк'),
    )
    vote_type = forms.ChoiceField(choices=VOTE_TYPES)

    def apply_vote(self, user, target_obj, like_model, target_field):
        value = 1 if self.cleaned_data['vote_type'] == 'like' else -1
        lookup = {'user': user, target_field: target_obj}

        with transaction.atomic():
            existing = like_model.objects.filter(**lookup).first()
            if existing:
                if existing.value == value:
                    delta = -value
                    existing.delete()
                    new_vote = 0
                else:
                    delta = value - existing.value
                    existing.value = value
                    existing.save(update_fields=['value'])
                    new_vote = value
            else:
                delta = value
                like_model.objects.create(**lookup, value=value)
                new_vote = value

            target_obj.__class__.objects.filter(pk=target_obj.pk).update(
                rating=F('rating') + delta
            )
            target_obj.refresh_from_db(fields=['rating'])

        return target_obj.rating, new_vote


class CorrectAnswerForm(forms.Form):
    answer_id = forms.IntegerField(min_value=1)

    def __init__(self, *args, question=None, **kwargs):
        self.question = question
        super().__init__(*args, **kwargs)

    def clean_answer_id(self):
        answer_id = self.cleaned_data['answer_id']
        answer = Answer.objects.filter(pk=answer_id, question=self.question).first()
        if answer is None:
            raise ValidationError('Ответ не найден в рамках этого вопроса.')
        self.answer_obj = answer
        return answer_id

    def save(self):
        with transaction.atomic():
            new_state = not self.answer_obj.is_correct
            if new_state:
                Answer.objects.filter(question=self.question, is_correct=True).update(is_correct=False)
            self.answer_obj.is_correct = new_state
            self.answer_obj.save(update_fields=['is_correct'])
        return self.answer_obj