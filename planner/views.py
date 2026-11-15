from calendar import Calendar
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import TaskForm, SubjectForm, ProfileForm
from .models import Subject, Task, StudentProfile
from django.contrib import messages


def user_subjects(request):
    return Subject.objects.filter(owner=request.user)


def user_tasks(request):
    return Task.objects.filter(subject__owner=request.user).select_related('subject')


@login_required
def home(request):
    today = timezone.localdate()
    all_tasks = user_tasks(request)
    completed = all_tasks.filter(status='completed')
    unfinished = all_tasks.exclude(status='completed')
    active = unfinished.filter(deadline__gte=today)
    overdue = unfinished.filter(deadline__lt=today)
    total_count = all_tasks.count()
    completed_count = completed.count()
    progress = round(completed_count / total_count * 100) if total_count else 0
    return render(request, 'planner/home.html', {
        'total_count': total_count,
        'completed_count': completed_count,
        'active_count': active.count(),
        'overdue_count': overdue.count(),
        'progress': progress,
        'upcoming_tasks': active.order_by('deadline')[:5],
        'subjects': user_subjects(request),
    })



@login_required
def tasks(request):
    today = timezone.localdate()
    task_list = user_tasks(request)
    subject_list = user_subjects(request)

    search = request.GET.get('q', '').strip()
    selected = request.GET.get('status', 'all')
    selected_subject = request.GET.get('subject', '')
    selected_priority = request.GET.get('priority', '')
    selected_sort = request.GET.get('sort', 'nearest')

    if selected == 'completed':
        task_list = task_list.filter(status='completed')

    elif selected == 'active':
        task_list = task_list.exclude(status='completed').filter(
            deadline__gte=today
        )

    elif selected == 'overdue':
        task_list = task_list.exclude(status='completed').filter(
            deadline__lt=today
        )

    if selected_subject in {str(s.pk) for s in subject_list}:
        task_list = task_list.filter(subject_id=selected_subject)

    if selected_priority in ['low', 'medium', 'high']:
        task_list = task_list.filter(priority=selected_priority)

    if selected_sort == 'latest':
        task_list = task_list.order_by('-deadline', 'title')

    elif selected_sort == 'name':
        task_list = task_list.order_by('title')

    else:
        task_list = task_list.order_by('deadline', 'title')

    # Поиск без учёта регистра, включая кириллицу
    if search:
        query = search.casefold()

        task_list = [
            task for task in task_list
            if query in task.title.casefold()
            or query in task.description.casefold()
        ]

    return render(request, 'planner/tasks.html', {
        'tasks': task_list,
        'subjects': subject_list,
        'today': today,
        'search': search,
        'selected': selected,
        'selected_subject': selected_subject,
        'selected_priority': selected_priority,
        'selected_sort': selected_sort,
    })



@login_required
def subjects(request):
    subject_list = user_subjects(request).annotate(
        task_count=Count('tasks'),
        completed_count=Count('tasks', filter=Q(tasks__status='completed')),
    )
    return render(request, 'planner/subjects.html', {'subjects': subject_list})


@login_required
def calendar(request):
    today = timezone.localdate()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if not 1900 <= year <= 2100:
            raise ValueError
        first_day = date(year, month, 1)
    except ValueError:
        year, month = today.year, today.month
        first_day = today.replace(day=1)
    previous_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1)
    default_day = today.day if (year == today.year and month == today.month) else 1
    try:
        selected_date = date(year, month, int(request.GET.get('day', default_day)))
    except ValueError:
        selected_date = date(year, month, default_day)
    monthly_tasks = user_tasks(request).filter(
        deadline__gte=first_day, deadline__lt=next_month
    ).order_by('deadline', 'title')
    tasks_by_date = {}
    for task in monthly_tasks:
        tasks_by_date.setdefault(task.deadline, []).append(task)
    weeks = []
    for week in Calendar(firstweekday=0).monthdatescalendar(year, month):
        days = []
        for current_date in week:
            days.append({
                'date': current_date, 'in_month': current_date.month == month,
                'tasks': tasks_by_date.get(current_date, []),
            })
        weeks.append(days)
    return render(request, 'planner/calendar.html', {
        'year': year, 'month': month, 'first_day': first_day,
        'previous_month': previous_month if previous_month.year >= 1900 else None,
        'next_month': next_month if next_month.year <= 2100 else None,
        'weeks': weeks, 'today': today, 'selected_date': selected_date,
        'selected_tasks': tasks_by_date.get(selected_date, []),
    })


@login_required
def radar(request):
    today = timezone.localdate()
    end_date = today + timedelta(days=6)
    saved_limit = StudentProfile.objects.filter(
        user=request.user
    ).values_list('daily_hours', flat=True).first() or 4

    try:
        daily_limit = int(request.GET.get('hours', saved_limit))
    except (ValueError, TypeError):
        daily_limit = saved_limit
    daily_limit = max(1, min(12, daily_limit))
    capacity = Decimal(daily_limit)
    zero = Decimal('0')

    # Получаем невыполненные задания текущего пользователя
    unfinished = list(user_tasks(request).exclude(status='completed')
                      .filter(deadline__lte=end_date).order_by('deadline', 'title', 'pk'))
    overdue_tasks = [task for task in unfinished if task.deadline < today]
    upcoming_tasks = [task for task in unfinished if task.deadline >= today]
    overdue_hours = sum((task.estimated_hours for task in overdue_tasks), zero)
    total_hours = sum((task.estimated_hours for task in unfinished), zero)
    available_hours = capacity * 7

    # Очередь заданий по срокам сдачи
    queue = [{'task': task, 'remaining': task.estimated_hours} for task in unfinished]
    position = 0
    cumulative_hours = overdue_hours
    days = []
    for offset in range(7):
        current_date = today + timedelta(days=offset)
        day_tasks = [task for task in upcoming_tasks if task.deadline == current_date]
        due_hours = sum((task.estimated_hours for task in day_tasks), zero)
        cumulative_hours += due_hours
        shortfall = max(zero, cumulative_hours - capacity * (offset + 1))
        budget = capacity
        plan = []
        while budget > 0 and position < len(queue):
            item = queue[position]
            hours = min(budget, item['remaining'])
            plan.append({'task': item['task'], 'hours': hours,
                         'late': item['task'].deadline < current_date})
            item['remaining'] -= hours
            budget -= hours
            if item['remaining'] == 0:
                position += 1
        days.append({
            'date': current_date, 'due_hours': due_hours, 'task_count': len(day_tasks),
            'overload': due_hours > capacity, 'shortfall': shortfall,
            'planned_hours': capacity - budget, 'plan': plan,
        })
    peak = max(days, key=lambda day: day['due_hours'])
    max_shortfall = max(day['shortfall'] for day in days)
    remaining_hours = sum((item['remaining'] for item in queue), zero)
    chart_max = max([capacity] + [day['due_hours'] for day in days])
    limit_width = int(capacity / chart_max * 100)
    for day in days:
        day['bar_width'] = int(day['due_hours'] / chart_max * 100)
    return render(request, 'planner/radar.html', {
        'today': today, 'end_date': end_date, 'daily_limit': daily_limit,
        'total_hours': total_hours, 'available_hours': available_hours,
        'overdue_hours': overdue_hours, 'overdue_tasks': overdue_tasks,
        'days': days, 'peak': peak, 'max_shortfall': max_shortfall,
        'remaining_hours': remaining_hours, 'limit_width': limit_width,
    })



@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)

        if form.is_valid():
            task = form.save()
            return redirect('planner:task_detail', task_id=task.pk)

    else:
        initial = {}

        try:
            initial['deadline'] = date.fromisoformat(
                request.GET.get('deadline', '')
            )
        except ValueError:
            pass

        subject_id = request.GET.get('subject', '')

        if subject_id in {
            str(subject.pk) for subject in user_subjects(request)
        }:
            initial['subject'] = subject_id

        form = TaskForm(initial=initial, user=request.user)

    return render(request, 'planner/task_form.html', {
        'form': form,
        'title': 'Новое задание',
    })



@login_required
def task_detail(request, task_id):
    task = get_object_or_404(user_tasks(request), pk=task_id)
    return render(request, 'planner/task_detail.html', {'task': task, 'today': timezone.localdate()})


@login_required
def task_update(request, task_id):
    task = get_object_or_404(user_tasks(request), pk=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('planner:task_detail', task_id=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user)
    return render(request, 'planner/task_form.html', {'form': form, 'title': 'Редактирование задания'})


@login_required
def task_delete(request, task_id):
    task = get_object_or_404(user_tasks(request), pk=task_id)
    if request.method == 'POST':
        task.delete()
        return redirect('planner:tasks')
    return render(request, 'planner/task_confirm_delete.html', {'task': task})


@login_required
@require_POST
def task_complete(request, task_id):
    task = get_object_or_404(user_tasks(request), pk=task_id)
    task.status = 'completed'
    task.save(update_fields=['status'])
    return redirect('planner:task_detail', task_id=task.pk)


@login_required
def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.owner = request.user
            subject.save()
            return redirect('planner:subject_detail', subject_id=subject.pk)
    else:
        form = SubjectForm()
    return render(request, 'planner/subject_form.html', {'form': form, 'title': 'Новая дисциплина'})


@login_required
def subject_detail(request, subject_id):
    subject = get_object_or_404(user_subjects(request), pk=subject_id)
    return render(request, 'planner/subject_detail.html', {
        'subject': subject, 'tasks': subject.tasks.all(), 'today': timezone.localdate(),
    })


@login_required
def subject_update(request, subject_id):
    subject = get_object_or_404(user_subjects(request), pk=subject_id)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('planner:subject_detail', subject_id=subject.pk)
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'planner/subject_form.html', {'form': form, 'title': 'Редактирование дисциплины'})


@login_required
def subject_delete(request, subject_id):
    subject = get_object_or_404(user_subjects(request), pk=subject_id)
    if request.method == 'POST':
        try:
            subject.delete()
            return redirect('planner:subjects')
        except ProtectedError:
            pass
    return render(request, 'planner/subject_confirm_delete.html', {
        'subject': subject, 'task_count': subject.tasks.count(),
    })


def register(request):
    if request.user.is_authenticated:
        return redirect('planner:home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('planner:home')
    else:
        form = UserCreationForm()
    return render(request, 'planner/auth.html', {'form': form, 'is_register': True})



@login_required
def profile(request):
    student_profile, created = StudentProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=student_profile)

        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки успешно сохранены.')
            return redirect('planner:profile')
    else:
        form = ProfileForm(instance=student_profile)

    all_tasks = user_tasks(request)

    return render(request, 'planner/profile.html', {
        'form': form,
        'student_profile': student_profile,
        'subject_count': user_subjects(request).count(),
        'task_count': all_tasks.count(),
        'completed_count': all_tasks.filter(status='completed').count(),
    })
