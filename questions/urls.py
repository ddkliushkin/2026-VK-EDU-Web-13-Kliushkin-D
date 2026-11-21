from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('question/<int:question_id>/vote/', views.vote_question, name='vote_question'),
    path('question/<int:question_id>/correct/', views.mark_correct, name='mark_correct'),
    path('answer/<int:answer_id>/vote/', views.vote_answer, name='vote_answer'),
    path('ask/', views.ask, name='ask'),
]