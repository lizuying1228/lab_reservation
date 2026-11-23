from django.contrib import admin, messages
from reservations.models import Reservation
from reservations.services import review_reservation
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError

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

    actions = [
        "approve_reservations",
        "reject_reservations",
    ]

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        raise PermissionDenied("预约记录不能直接修改，请使用审核操作")

    # 审核通过
    @admin.action(description="审核通过所选预约")
    def approve_reservations(self, request, queryset):
        self._review_reservations(
            request,
            queryset,
            Reservation.StatusChoices.APPROVED,
        )

    # 审核拒绝
    @admin.action(description="审核拒绝所选预约")
    def reject_reservations(self, request, queryset):
        self._review_reservations(
            request,
            queryset,
            Reservation.StatusChoices.REJECTED,
        )

    # 统一处理审核
    def _review_reservations(self, request, queryset, target_status):
        success_count = 0
        failed_count = 0

        for reservation in queryset:
            try:
                review_reservation(
                    reservation_id=reservation.id,
                    target_status=target_status,
                    operator_id=request.user.id
                )
                success_count += 1

            except ValidationError as exc:
                failed_count += 1
                self.message_user(
                    request,
                    f"预约 ID={reservation.id} 审核失败：{exc.detail}",
                    level=messages.WARNING,
                )

        if success_count:
            self.message_user(
                request,
                f"成功处理 {success_count} 条预约。",
                level=messages.SUCCESS,
            )

        if failed_count:
            self.message_user(
                request,
                f"有 {failed_count} 条预约处理失败，请查看具体原因。",
                level=messages.ERROR,
            )