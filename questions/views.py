from django.shortcuts import render, get_object_or_404
from .models import Question, Answer, Tag
from .utils import paginate


def index(request):
    page_obj = paginate(Question.objects.new(), request, per_page=10)
    return render(request, 'questions/index.html', {'page_obj': page_obj})


def hot(request):
    page_obj = paginate(Question.objects.hot(), request, per_page=10)
    return render(request, 'questions/hot.html', {'page_obj': page_obj})


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, name=tag_name)
    page_obj = paginate(Question.objects.by_tag(tag_obj), request, per_page=10)
    return render(request, 'questions/tag.html', {'tag_name': tag_obj.name, 'page_obj': page_obj})


def question(request, question_id):
    question_obj = get_object_or_404(Question.objects.with_details(), pk=question_id)
    page_obj = paginate(Answer.objects.for_question(question_obj), request, per_page=10)
    return render(request, 'questions/question.html', {'question': question_obj, 'page_obj': page_obj})


def ask(request):
    return render(request, 'questions/ask.html')