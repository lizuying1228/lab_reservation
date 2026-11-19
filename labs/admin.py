from django.contrib import admin
from labs.models import Laboratory
# Register your models here.
@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ["lab_no", "position", "labadmin", "status", "is_deleted"]
    search_fields = ["lab_no", "position"]
    list_filter = ["status", "is_deleted"]
    ordering = ["lab_no"]
    readonly_fields = ["is_deleted", "deleted_at"]

    def has_delete_permission(self, request, obj=None):
        return False