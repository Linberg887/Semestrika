
from django.shortcuts import render


def home(request):
    return render(request, 'planner/home.html')


def tasks(request):
    return render(request, 'planner/section.html', {
        'title': 'Мои задания',
        'description': 'Планируй задания и контролируй сроки сдачи.',
        'message': 'Здесь будут отображаться твои учебные задания.',
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
