from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class Subject(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='subjects',
        verbose_name='Владелец',
        null=False
    )

    name = models.CharField('Название', max_length=150)
    teacher = models.CharField(
        'Преподаватель', max_length=150, blank=True
    )
    description = models.TextField('Описание', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Дисциплина'
        verbose_name_plural = 'Дисциплины'
        ordering = ['name']
class Task(models.Model):

    STATUS_CHOICES = [
        ('new', 'Не начато'),
        ('in_progress', 'В процессе'),
        ('completed', 'Выполнено'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='tasks',
        verbose_name='Дисциплина'
    )

    title = models.CharField('Название задания', max_length=200)
    description = models.TextField('Описание', blank=True)
    deadline = models.DateField('Срок сдачи')

    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )

    priority = models.CharField(
        'Приоритет',
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    estimated_hours = models.DecimalField(
        'Время выполнения (часы)',
        max_digits=4,
        decimal_places=1,
        default=1,
        validators=[
            MinValueValidator(0.5),
            MaxValueValidator(100)
        ]
    )

    created_at = models.DateTimeField(
        'Дата создания', auto_now_add=True
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Учебное задание'
        verbose_name_plural = 'Учебные задания'
        ordering = ['deadline']
