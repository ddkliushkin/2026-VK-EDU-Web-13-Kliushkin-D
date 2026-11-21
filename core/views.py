from django.shortcuts import render
from questions.views import get_base_context


def login_view(request):
    return render(request, 'core/login.html', get_base_context())


def signup_view(request):
    return render(request, 'core/signup.html', get_base_context())


def profile_view(request):
    return render(request, 'core/profile.html', get_base_context())