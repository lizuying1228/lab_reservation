from django.contrib import admin
from lab_admins.models import LabAdmin
# Register your models here.
@admin.register(LabAdmin)
class LabAdminAdmin(admin.ModelAdmin):
    list_display = ["name", "admin_no", "birth_date", "user", "is_deleted"]
    search_fields = ["name", "admin_no"]
    ordering = ["admin_no"]
    readonly_fields = ["is_deleted", "deleted_at"]
    list_filter = ["is_deleted"]

    def has_delete_permission(self, request, obj = None):
        return False