from django.contrib import admin
from reservation_times.models import ReservationTime

# Register your models here.
@admin.register(ReservationTime)
class ReservationTimeAdmin(admin.ModelAdmin):
    readonly_fields = ["is_deleted", "deleted_at"]
    list_filter = ["date", "time", "status", "is_deleted"]
    list_display = ["lab", "date", "time", "status", "is_deleted"]
    search_fields = ["lab__lab_no", "lab__position"]
    ordering = ["date", "time"]
    date_hierarchy = "date"

    def has_delete_permission(self, request, obj=None):
        return False