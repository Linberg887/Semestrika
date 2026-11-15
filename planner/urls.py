
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'planner'

urlpatterns = [
    path('', views.home, name='home'),

    path('tasks/', views.tasks, name='tasks'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/<int:task_id>/edit/', views.task_update, name='task_update'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:task_id>/complete/', views.task_complete, name='task_complete'),

    path('subjects/', views.subjects, name='subjects'),
    path('subjects/create/', views.subject_create, name='subject_create'),
    path('subjects/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    path('subjects/<int:subject_id>/edit/', views.subject_update, name='subject_update'),
    path('subjects/<int:subject_id>/delete/', views.subject_delete, name='subject_delete'),

    path('calendar/', views.calendar, name='calendar'),
    path('radar/', views.radar, name='radar'),

    path('register/', views.register, name='register'),

    path('login/', auth_views.LoginView.as_view(
        template_name='planner/auth.html',
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
