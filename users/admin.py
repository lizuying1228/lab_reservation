from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from users.services import delete_user

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    readonly_fields = ["is_deleted", "deleted_at"]

    list_display = [
        "username",
        "phone",
        "email",
        "is_active",
        "is_staff",
        "is_deleted",
    ]

    search_fields = [
        "username",
        "phone",
        "email",
    ]

    list_filter = [
        "is_active",
        "is_staff",
        "is_deleted",
    ]

    ordering = ["username"]

    fieldsets = (
        *(UserAdmin.fieldsets or ()),
        ("联系信息", {"fields": ("phone",)}),
    )

    add_fieldsets = (
        *(UserAdmin.add_fieldsets or ()),
        ("联系信息", {"fields": ("phone",)}),
    )

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

    def delete_model(self, request, obj):
        """单个用户删除：调用 Service 执行软删除。"""
        try:
            delete_user(
                target_user_id=obj.id,
                operator_id=request.user.id,
            )
        except DRFValidationError as exc:
            raise DjangoValidationError(str(exc.detail)) from exc

    def delete_queryset(self, request, queryset):
        """批量用户删除：逐个调用 Service，不能使用 queryset.delete()。"""
        success_count = 0
        failed_count = 0

        for user_id in queryset.values_list("id", flat=True):
            try:
                delete_user(
                    target_user_id=user_id,
                    operator_id=request.user.id,
                )
                success_count += 1

            except DRFValidationError as exc:
                failed_count += 1
                self.message_user(
                    request,
                    f"用户 ID={user_id} 删除失败：{exc.detail}",
                    level=messages.WARNING,
                )

        if success_count:
            self.message_user(
                request,
                f"成功软删除 {success_count} 个用户。",
                level=messages.SUCCESS,
            )

        if failed_count:
            self.message_user(
                request,
                f"有 {failed_count} 个用户删除失败。",
                level=messages.ERROR,
            )