from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import QuestionForm, AnswerForm, VoteForm, CorrectAnswerForm
from .models import Question, Answer, Tag, QuestionLike, AnswerLike
from .utils import paginate

ANSWERS_PER_PAGE = 10


def _attach_user_votes(page_obj, user, like_model, field_name):
    if not user.is_authenticated:
        return
    ids = [obj.id for obj in page_obj]
    votes = dict(
        like_model.objects.filter(user=user, **{f'{field_name}_id__in': ids})
        .values_list(f'{field_name}_id', 'value')
    )
    for obj in page_obj:
        obj.user_vote = votes.get(obj.id, 0)


def index(request):
    page_obj = paginate(Question.objects.new(), request, per_page=10)
    _attach_user_votes(page_obj, request.user, QuestionLike, 'question')
    return render(request, 'questions/index.html', {'page_obj': page_obj})


def hot(request):
    page_obj = paginate(Question.objects.hot(), request, per_page=10)
    _attach_user_votes(page_obj, request.user, QuestionLike, 'question')
    return render(request, 'questions/hot.html', {'page_obj': page_obj})


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, name=tag_name)
    page_obj = paginate(Question.objects.by_tag(tag_obj), request, per_page=10)
    _attach_user_votes(page_obj, request.user, QuestionLike, 'question')
    return render(request, 'questions/tag.html', {'tag_name': tag_obj.name, 'page_obj': page_obj})


def question(request, question_id):
    question_obj = get_object_or_404(Question.objects.with_details(), pk=question_id)
    form = AnswerForm(request.POST or None)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        if form.is_valid():
            answer = form.save(question=question_obj, author=request.user)
            answer_ids = list(Answer.objects.for_question(question_obj).values_list('id', flat=True))
            position = answer_ids.index(answer.id)
            page_num = position // ANSWERS_PER_PAGE + 1
            return redirect(f'{question_obj.get_absolute_url()}?page={page_num}#answer-{answer.id}')

    page_obj = paginate(Answer.objects.for_question(question_obj), request, per_page=ANSWERS_PER_PAGE)
    _attach_user_votes(page_obj, request.user, AnswerLike, 'answer')
    if request.user.is_authenticated:
        vote = QuestionLike.objects.filter(user=request.user, question=question_obj).first()
        question_obj.user_vote = vote.value if vote else 0

    return render(request, 'questions/question.html', {
        'question': question_obj,
        'page_obj': page_obj,
        'form': form,
    })


@login_required
def ask(request):
    form = QuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_question = form.save(author=request.user)
        return redirect(new_question.get_absolute_url())
    return render(request, 'questions/ask.html', {'form': form})


def vote_question(request, question_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Разрешён только метод POST.'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Войдите, чтобы голосовать.', 'login_url': reverse('login')}, status=401)

    question_obj = Question.objects.filter(pk=question_id).first()
    if question_obj is None:
        return JsonResponse({'error': 'Вопрос не найден.'}, status=404)

    form = VoteForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Некорректные параметры голосования.'}, status=400)

    try:
        rating, user_vote = form.apply_vote(request.user, question_obj, QuestionLike, 'question')
    except ValidationError as exc:
        return JsonResponse({'error': exc.message}, status=400)

    return JsonResponse({'rating': rating, 'user_vote': user_vote})


def vote_answer(request, answer_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Разрешён только метод POST.'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Войдите, чтобы голосовать.', 'login_url': reverse('login')}, status=401)

    answer_obj = Answer.objects.filter(pk=answer_id).first()
    if answer_obj is None:
        return JsonResponse({'error': 'Ответ не найден.'}, status=404)

    form = VoteForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Некорректные параметры голосования.'}, status=400)

    try:
        rating, user_vote = form.apply_vote(request.user, answer_obj, AnswerLike, 'answer')
    except ValidationError as exc:
        return JsonResponse({'error': exc.message}, status=400)

    return JsonResponse({'rating': rating, 'user_vote': user_vote})


def mark_correct(request, question_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Разрешён только метод POST.'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Требуется авторизация.', 'login_url': reverse('login')}, status=401)

    question_obj = Question.objects.filter(pk=question_id).first()
    if question_obj is None:
        return JsonResponse({'error': 'Вопрос не найден.'}, status=404)
    if question_obj.author_id != request.user.id:
        return JsonResponse({'error': 'Только автор вопроса может отмечать правильный ответ.'}, status=403)

    form = CorrectAnswerForm(request.POST, question=question_obj)
    if not form.is_valid():
        return JsonResponse({'error': 'Некорректный ID ответа.'}, status=400)

    answer = form.save()
    return JsonResponse({'answer_id': answer.id, 'is_correct': answer.is_correct})