from django.shortcuts import render
from django.http import Http404
from .utils import paginate

POPULAR_TAGS = [
    {'name': 'поиск_ошибки', 'color': 'text-bg-primary'},
    {'name': 'теория', 'color': 'text-bg-success'},
    {'name': 'оффтоп', 'color': 'text-bg-danger'},
    {'name': 'что_поиграть', 'color': 'text-bg-warning'},
    {'name': 'железо', 'color': 'text-bg-info'},
    {'name': 'лайфхак', 'color': 'text-bg-secondary'},
    {'name': 'алгоритмы', 'color': 'text-bg-dark'},
    {'name': 'история', 'color': 'text-bg-light border text-dark'},
]

TAG_NAMES = [t['name'] for t in POPULAR_TAGS]

BEST_MEMBERS = [
    'XenoBlast',
    'CyberMantis',
    'SilverKite',
    'NeonVanguard',
    'EchoDrifter',
]

QUESTIONS = [
    {
        'id': i,
        'title': f'Вопрос #{i}: Lorem ipsum dolor sit amet, consectetur adipiscing elit?',
        'text': f'Текст вопроса #{i}. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
        'author': BEST_MEMBERS[i % len(BEST_MEMBERS)],
        'created_at': f'{i * 5} минут назад',
        'rating': (i * 7) % 25 - 5,
        'answers_count': (i * 3) % 15 + 1,
        'tags': [
            TAG_NAMES[i % len(TAG_NAMES)],
            TAG_NAMES[(i + 1) % len(TAG_NAMES)],
            TAG_NAMES[(i + 2) % len(TAG_NAMES)],
        ],
    }
    for i in range(1, 35)
]


def get_base_context():
    return {
        'popular_tags': POPULAR_TAGS,
        'best_members': BEST_MEMBERS,
    }


def index(request):
    page_obj = paginate(QUESTIONS, request, per_page=5)
    context = {
        **get_base_context(),
        'page_obj': page_obj,
    }
    return render(request, 'questions/index.html', context)


def hot(request):
    hot_questions = sorted(QUESTIONS, key=lambda q: q['rating'], reverse=True)
    page_obj = paginate(hot_questions, request, per_page=5)
    context = {
        **get_base_context(),
        'page_obj': page_obj,
    }
    return render(request, 'questions/hot.html', context)


def tag(request, tag_name):
    filtered = [q for q in QUESTIONS if tag_name in q['tags']]
    page_obj = paginate(filtered, request, per_page=5)
    context = {
        **get_base_context(),
        'tag_name': tag_name,
        'page_obj': page_obj,
    }
    return render(request, 'questions/tag.html', context)


def question(request, question_id):
    item = next((q for q in QUESTIONS if q['id'] == question_id), None)
    if item is None:
        raise Http404('Вопрос не найден')

    answers = [
        {
            'id': j,
            'author': BEST_MEMBERS[j % len(BEST_MEMBERS)],
            'text': f'Ответ #{j} на вопрос #{question_id}. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
            'created_at': f'{j * 3} минут назад',
            'rating': 10 - j,
            'is_correct': j == 1,
        }
        for j in range(1, 16)
    ]

    page_obj = paginate(answers, request, per_page=5)
    context = {
        **get_base_context(),
        'question': item,
        'page_obj': page_obj,
    }
    return render(request, 'questions/question.html', context)


def ask(request):
    return render(request, 'questions/ask.html', get_base_context())