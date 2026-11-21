from django.contrib.auth.models import User
from questions.models import Tag


def sidebar_data(request):
    return {
        'popular_tags': Tag.objects.all()[:10],
        'best_members': User.objects.all()[:5],
    }