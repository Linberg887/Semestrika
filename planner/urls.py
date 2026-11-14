from django.urls import path
from . import views

app_name = 'planner'

urlpatterns = [
    path('', views.home, name='home'),
    path('tasks/', views.tasks, name='tasks'),
    path('subjects/', views.subjects, name='subjects'),
    path('calendar/', views.calendar, name='calendar'),
    path('radar/', views.radar, name='radar'),
]