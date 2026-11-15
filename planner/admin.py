
from django.contrib import admin
from .models import Subject, Task


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher')
    search_fields = ('name', 'teacher')


class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'subject',
        'deadline',
        'status',
        'priority',
        'estimated_hours'
    )

    list_filter = ('subject', 'status', 'priority')
    search_fields = ('title', 'description')
    ordering = ('deadline',)


admin.site.register(Subject, SubjectAdmin)
admin.site.register(Task, TaskAdmin)

admin.site.site_header = 'Semestrika — управление'
admin.site.site_title = 'Semestrika Admin'
admin.site.index_title = 'Панель управления'
