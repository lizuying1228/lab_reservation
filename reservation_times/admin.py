from django.contrib import admin
from reservation_times.models import ReservationTime
from reservation_times.services import create_reservationtime, update_reservationtime, delete_reservationtime

# Register your models here.
@admin.register(ReservationTime)
class ReservationTimeAdmin(admin.ModelAdmin):
    readonly_fields = ["is_deleted", "deleted_at"]
    list_filter = ["date", "time", "status", "is_deleted"]
    list_display = ["lab", "date", "time", "status", "is_deleted"]
    search_fields = ["lab__lab_no", "lab__position"]
    ordering = ["date", "time"]
    date_hierarchy = "date"

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if change:
            reservationtime = update_reservationtime(
                reservationtime_id=obj.id,
                validated_data={
                    "lab": obj.lab,
                    "date": obj.date,
                    "time": obj.time
                },
                operator_id=request.user.id
            )
        else:
            reservationtime = create_reservationtime(
                validated_data={
                    "lab_no": obj.lab.lab_no,
                    "date": obj.date,
                    "time": obj.time
                },
                operator_id=request.user.id
            )
        obj.pk = reservationtime.pk
        obj.refresh_from_db()

    def delete_model(self, request, obj):
        delete_reservationtime(reservationtime_id=obj.id, operator_id=request.user.id)

    def delete_queryset(self, request, queryset):
        for reservationtime_id in queryset.filter(is_deleted=False).values_list("id", flat=True):
            delete_reservationtime(reservationtime_id=reservationtime_id, operator_id=request.user.id)
