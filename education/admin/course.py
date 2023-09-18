from django.contrib import admin

from education.models import Course

class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_public', 'is_locked')
    list_filter = ('is_public', 'is_locked')
    search_fields = ('name',)
    