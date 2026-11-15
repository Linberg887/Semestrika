from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Subject, Task
from .forms import TaskForm
from django.views.decorators.http import require_POST
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
    selected = request.GET.get('status', 'all')

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

    return render(request, 'planner/tasks.html', {
        'tasks': task_list,
        'today': today,
    })


def subjects(request):
    return render(request, 'planner/section.html', {
        'title': 'Мои дисциплины',
        'description': 'Организуй учебные предметы в одном месте.',
        'message': 'Здесь будут отображаться твои дисциплины.',
    })


def calendar(request):
    return render(request, 'planner/section.html', {
        'title': 'Учебный календарь',
        'description': 'Не упускай важные даты.',
        'message': 'Здесь появится календарь учебных заданий.',
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
        form = TaskForm()

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
