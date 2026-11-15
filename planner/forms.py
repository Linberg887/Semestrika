
from django import forms
from .models import Task, Subject


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task

        fields = [
            'title',
            'subject',
            'description',
            'deadline',
            'priority',
            'status',
            'estimated_hours',
        ]

        widgets = {
            'deadline': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
            'description': forms.Textarea(
                attrs={'rows': 4}
            ),
            'title': forms.TextInput(
                attrs={'placeholder': 'Например, подготовить доклад'}
            ),
        }

        help_texts = {
            'estimated_hours': (
                'Укажи примерное время от 0,5 до 100 часов. '
                'Оно используется для расчёта учебной нагрузки.'
            ),
        }



class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject

        fields = [
            'name',
            'teacher',
            'description',
        ]

        widgets = {
            'name': forms.TextInput(
                attrs={'placeholder': 'Например, финансовый менеджмент'}
            ),
            'teacher': forms.TextInput(
                attrs={'placeholder': 'ФИО преподавателя'}
            ),
            'description': forms.Textarea(
                attrs={'rows': 4}
            ),
        }
