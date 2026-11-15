
from django import forms
from .models import Task, Subject, StudentProfile


class TaskForm(forms.ModelForm):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(
            owner=user
        )

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



class ProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile

        fields = [
            'display_name',
            'daily_hours',
        ]

        widgets = {
            'display_name': forms.TextInput(
                attrs={'placeholder': 'Как к тебе обращаться?'}
            ),
            'daily_hours': forms.NumberInput(
                attrs={'min': 1, 'max': 12, 'step': 1}
            ),
        }

        help_texts = {
            'daily_hours': 'Используется в Semestrika Radar.',
        }
