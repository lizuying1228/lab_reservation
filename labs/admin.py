from django.contrib import admin
from labs.models import Laboratory
from labs.services import (
    create_laboratory,
    update_laboratory,
    delete_laboratory,
)


@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):

    list_display = [
        "lab_no",
        "position",
        "labadmin",
        "status",
        "is_deleted",
    ]

    search_fields = ["lab_no", "position"]

    list_filter = ["status", "is_deleted"]

    ordering = ["lab_no"]

    readonly_fields = [
        "is_deleted",
        "deleted_at",
    ]

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
            lab = update_laboratory(
                lab_id=obj.id,
                validated_data={
                    "position": obj.position,
                    "status": obj.status,
                    "labadmin": obj.labadmin,
                },
                operator_id=request.user.id,
            )
        else:
            lab = create_laboratory(
                validated_data={
                    "lab_no": obj.lab_no,
                    "position": obj.position,
                    "status": obj.status,
                    "labadmin_admin_no": obj.labadmin.admin_no,
                },
                operator_id=request.user.id,
            )
        obj.pk = lab.pk
        obj.refresh_from_db()

    def delete_model(self, request, obj):
        delete_laboratory(
            lab_id=obj.id,
            operator_id=request.user.id,
        )

    def delete_queryset(self, request, queryset):
        for obj in queryset.order_by("id"):
            delete_laboratory(
                lab_id=obj.id,
                operator_id=request.user.id,
            )
