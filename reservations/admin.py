from django.contrib import admin
from reservations.models import Reservation

# Register your models here.
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "reservationtime",
        "status",
        "created_at",
    ]

    search_fields = [
        "student__name",
        "student__student_no",
        "reservationtime__lab__lab_no",
    ]

    list_filter = ["status", "created_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    readonly_fields = [
        "student",
        "reservationtime",
        "status",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False