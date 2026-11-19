from django.contrib import admin
from students.models import Student

# Register your models here.
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    readonly_fields = ["is_deleted", "deleted_at"]

    list_display = ["name", "student_no", "birth_date", "user", "is_deleted"]
    search_fields = ["name", "student_no"]
    list_filter = ["is_deleted"]
    ordering = ["student_no"]
    
    def has_delete_permission(self, request, obj=None):
        return False