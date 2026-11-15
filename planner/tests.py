
from datetime import timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Subject, Task, StudentProfile


class SemestrikaTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username='student1',
            password='TestPassword123!'
        )

        self.other_user = User.objects.create_user(
            username='student2',
            password='TestPassword456!'
        )

        self.subject = Subject.objects.create(
            name='Веб-разработка',
            owner=self.user
        )

        self.other_subject = Subject.objects.create(
            name='Экономика',
            owner=self.other_user
        )

        self.deadline = timezone.localdate() + timedelta(days=1)

        self.task = Task.objects.create(
            title='Подготовить презентацию',
            subject=self.subject,
            deadline=self.deadline,
            estimated_hours=7
        )

        self.other_task = Task.objects.create(
            title='Чужое задание',
            subject=self.other_subject,
            deadline=self.deadline,
            estimated_hours=20
        )

        self.client.force_login(self.user)

    def task_data(self, **changes):
        data = {
            'title': 'Новое задание',
            'subject': self.subject.pk,
            'description': 'Тестовое описание',
            'deadline': self.deadline.isoformat(),
            'priority': 'medium',
            'status': 'new',
            'estimated_hours': '2',
        }

        data.update(changes)
        return data

    # Проверка авторизации

    def test_guest_access(self):
        self.client.logout()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_registration(self):
        self.client.logout()

        self.client.post('/register/', {
            'username': 'newstudent',
            'password1': 'StrongPassword789!',
            'password2': 'StrongPassword789!',
        })

        user = get_user_model().objects.get(
            username='newstudent'
        )

        self.assertTrue(
            user.check_password('StrongPassword789!')
        )

    def test_login_and_logout(self):
        self.client.logout()

        response = self.client.post('/login/', {
            'username': 'student1',
            'password': 'TestPassword123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get('/').status_code, 200)

        self.client.post('/logout/')
        self.assertEqual(self.client.get('/').status_code, 302)

    # Проверка безопасности

    def test_private_data(self):
        response = self.client.get('/tasks/')

        self.assertContains(response, self.task.title)
        self.assertNotContains(response, self.other_task.title)

        response = self.client.get(
            f'/tasks/{self.other_task.pk}/'
        )

        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            f'/tasks/{self.other_task.pk}/delete/'
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            Task.objects.filter(pk=self.other_task.pk).exists()
        )

    def test_foreign_subject_validation(self):
        response = self.client.post(
            '/tasks/create/',
            self.task_data(subject=self.other_subject.pk)
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Task.objects.filter(title='Новое задание').exists()
        )

    # Проверка управления заданиями

    def test_task_creation(self):
        response = self.client.post(
            '/tasks/create/',
            self.task_data()
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Task.objects.filter(
                title='Новое задание',
                subject=self.subject
            ).exists()
        )

    def test_invalid_hours(self):
        response = self.client.post(
            '/tasks/create/',
            self.task_data(estimated_hours='-5')
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn(
            'estimated_hours',
            response.context['form'].errors
        )

        self.assertFalse(
            Task.objects.filter(title='Новое задание').exists()
        )

    def test_update_complete_delete(self):
        task_id = self.task.pk

        response = self.client.post(
            f'/tasks/{task_id}/edit/',
            self.task_data(title='Обновлённое задание')
        )

        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.title,
            'Обновлённое задание'
        )

        response = self.client.post(
            f'/tasks/{task_id}/complete/'
        )

        self.assertEqual(response.status_code, 302)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'completed')

        response = self.client.post(
            f'/tasks/{task_id}/delete/'
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Task.objects.filter(pk=task_id).exists()
        )

    # Проверка защиты дисциплин

    def test_protected_subject(self):
        self.client.post(
            f'/subjects/{self.subject.pk}/delete/'
        )

        self.assertTrue(
            Subject.objects.filter(pk=self.subject.pk).exists()
        )

    # Проверка поиска

    def test_search(self):
        response = self.client.get(
            '/tasks/',
            {'q': 'ПРЕЗЕНТАЦИЮ'}
        )

        self.assertContains(response, self.task.title)
        self.assertNotContains(response, self.other_task.title)

    # Проверка календаря

    def test_calendar(self):
        response = self.client.get('/calendar/', {
            'year': self.deadline.year,
            'month': self.deadline.month,
            'day': self.deadline.day,
        })

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, self.task.title)
        self.assertNotContains(response, self.other_task.title)

    # Проверка Semestrika Radar

    def test_radar_calculation(self):
        response = self.client.get('/radar/', {'hours': 2})

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['total_hours'], 7)
        self.assertEqual(response.context['available_hours'], 14)
        self.assertEqual(response.context['peak']['due_hours'], 7)
        self.assertEqual(response.context['max_shortfall'], 3)

        self.task.status = 'completed'
        self.task.save()

        response = self.client.get('/radar/', {'hours': 2})

        self.assertEqual(response.context['total_hours'], 0)

    # Проверка персональных настроек

    def test_profile_settings(self):
        response = self.client.post('/profile/', {
            'display_name': 'Тестовый студент',
            'daily_hours': 6,
        })

        self.assertEqual(response.status_code, 302)

        profile = StudentProfile.objects.get(user=self.user)

        self.assertEqual(profile.display_name, 'Тестовый студент')
        self.assertEqual(profile.daily_hours, 6)

        response = self.client.get('/radar/')

        self.assertEqual(response.context['daily_limit'], 6)
