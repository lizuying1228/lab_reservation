from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()
# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    readonly_fields = ["is_deleted", "deleted_at"]

    list_display = [
        "username",
        "phone",
        "email",
        "is_active",
        "is_staff",
        "is_deleted"
    ]

    search_fields = [
        "username",
        "phone",
        "email",
    ]

    list_filter = [
        "is_active",
        "is_staff",
        "is_deleted"
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

    def has_delete_permission(self, request, obj=None):
        return False