from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Subject, Task
from .forms import TaskForm, SubjectForm
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST
from calendar import Calendar
from datetime import date, timedelta
def home(request):
    today = timezone.localdate()

    all_tasks = Task.objects.all()
    completed = all_tasks.filter(status='completed')
    unfinished = all_tasks.exclude(status='completed')

    active = unfinished.filter(deadline__gte=today)
    overdue = unfinished.filter(deadline__lt=today)

    total_count = all_tasks.count()
    completed_count = completed.count()

    progress = round(completed_count / total_count * 100) if total_count else 0

    context = {
        'total_count': total_count,
        'completed_count': completed_count,
        'active_count': active.count(),
        'overdue_count': overdue.count(),
        'progress': progress,
        'upcoming_tasks': active.order_by('deadline')[:5],
        'subjects': Subject.objects.all(),
    }

    return render(request, 'planner/home.html', context)



def tasks(request):
    today = timezone.localdate()
    task_list = Task.objects.select_related('subject').all()
    subject_list = Subject.objects.all()

    search = request.GET.get('q', '').strip()
    selected = request.GET.get('status', 'all')
    selected_subject = request.GET.get('subject', '')
    selected_priority = request.GET.get('priority', '')
    selected_sort = request.GET.get('sort', 'nearest')

    if search:
        task_list = task_list.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

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




def subjects(request):
    subject_list = Subject.objects.annotate(
        task_count=Count('tasks'),
        completed_count=Count(
            'tasks',
            filter=Q(tasks__status='completed')
        )
    )

    return render(request, 'planner/subjects.html', {
        'subjects': subject_list,
    })



def calendar(request):
    today = timezone.localdate()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))

        if not 1900 <= year <= 2100:
            raise ValueError

        first_day = date(year, month, 1)

    except ValueError:
        year = today.year
        month = today.month
        first_day = today.replace(day=1)

    previous_month = (
        first_day - timedelta(days=1)
    ).replace(day=1)

    next_month = (
        first_day.replace(day=28) + timedelta(days=4)
    ).replace(day=1)

    default_day = today.day if (
        year == today.year and month == today.month
    ) else 1

    try:
        selected_date = date(
            year, month,
            int(request.GET.get('day', default_day))
        )
    except ValueError:
        selected_date = date(year, month, default_day)

    monthly_tasks = Task.objects.select_related('subject').filter(
        deadline__gte=first_day,
        deadline__lt=next_month
    ).order_by('deadline', 'title')

    tasks_by_date = {}

    for task in monthly_tasks:
        tasks_by_date.setdefault(task.deadline, []).append(task)

    weeks = []

    for week in Calendar(firstweekday=0).monthdatescalendar(year, month):
        days = []

        for current_date in week:
            days.append({
                'date': current_date,
                'in_month': current_date.month == month,
                'tasks': tasks_by_date.get(current_date, []),
            })

        weeks.append(days)

    return render(request, 'planner/calendar.html', {
        'year': year,
        'month': month,
        'first_day': first_day,
        'previous_month': previous_month if previous_month.year >= 1900 else None,
        'next_month': next_month if next_month.year <= 2100 else None,
        'weeks': weeks,
        'today': today,
        'selected_date': selected_date,
        'selected_tasks': tasks_by_date.get(selected_date, []),
    })


def radar(request):
    return render(request, 'planner/section.html', {
        'title': 'Semestrika Radar',
        'description': 'Предусмотри нагрузку заранее.',
        'message': 'Здесь будет отображаться анализ учебной нагрузки.',
    })




def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)

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

        form = TaskForm(initial=initial)

    return render(request, 'planner/task_form.html', {
        'form': form,
        'title': 'Новое задание',
    })



def task_detail(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    return render(request, 'planner/task_detail.html', {
        'task': task,
        'today': timezone.localdate(),
    })



def task_update(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)

        if form.is_valid():
            form.save()
            return redirect('planner:task_detail', task_id=task.pk)
    else:
        form = TaskForm(instance=task)

    return render(request, 'planner/task_form.html', {
        'form': form,
        'title': 'Редактирование задания',
    })


def task_delete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    if request.method == 'POST':
        task.delete()
        return redirect('planner:tasks')

    return render(request, 'planner/task_confirm_delete.html', {
        'task': task,
    })


@require_POST
def task_complete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.status = 'completed'
    task.save(update_fields=['status'])

    return redirect('planner:task_detail', task_id=task.pk)



def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)

        if form.is_valid():
            subject = form.save()
            return redirect('planner:subject_detail', subject_id=subject.pk)
    else:
        form = SubjectForm()

    return render(request, 'planner/subject_form.html', {
        'form': form,
        'title': 'Новая дисциплина',
    })


def subject_detail(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    return render(request, 'planner/subject_detail.html', {
        'subject': subject,
        'tasks': subject.tasks.all(),
        'today': timezone.localdate(),
    })


def subject_update(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)

        if form.is_valid():
            form.save()
            return redirect('planner:subject_detail', subject_id=subject.pk)
    else:
        form = SubjectForm(instance=subject)

    return render(request, 'planner/subject_form.html', {
        'form': form,
        'title': 'Редактирование дисциплины',
    })


def subject_delete(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    if request.method == 'POST':
        try:
            subject.delete()
            return redirect('planner:subjects')
        except ProtectedError:
            pass

    return render(request, 'planner/subject_confirm_delete.html', {
        'subject': subject,
        'task_count': subject.tasks.count(),
    })
