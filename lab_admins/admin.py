from django.contrib import admin
from lab_admins.models import LabAdmin
from django import forms
from lab_admins.services import create_labadmin, update_labadmin, delete_labadmin

# Register your models here.
class LabAdminCreateAdminForm(forms.ModelForm):
    username = forms.CharField(required=True, max_length=150, label="用户名")
    password = forms.CharField(required=True, min_length=8, label="密码", widget=forms.PasswordInput)

    class Meta:
        model = LabAdmin
        fields = ["name", "admin_no", "birth_date"]

class LabAdminUpdateAdminForm(forms.ModelForm):
    class Meta:
        model = LabAdmin
        fields = ["name", "birth_date"]

@admin.register(LabAdmin)
class LabAdminAdmin(admin.ModelAdmin):
    list_display = ["name", "admin_no", "birth_date", "user", "is_deleted"]
    search_fields = ["name", "admin_no"]
    ordering = ["admin_no"]
    list_filter = ["is_deleted"]

    def get_readonly_fields(self, request, obj = ...):
        if obj is None:
            return ["is_deleted", "deleted_at"]
        return ["admin_no", "user", "is_deleted", "deleted_at"]

    def get_form(self, request, obj = ..., **kwargs):
        if obj is None:
            kwargs["form"] = LabAdminCreateAdminForm
        else:
            kwargs["form"] = LabAdminUpdateAdminForm

        return super().get_form(request, obj, **kwargs)

    def get_fields(self, request, obj = ...):
        if obj is None:
            return ["name", "admin_no", "birth_date", "username", "password"]
        return ["name", "admin_no", "birth_date", "user", "is_deleted", "deleted_at"]

    def save_model(self, request, obj, form, change):
        if not change:
            labadmin = create_labadmin(validated_data={
                "name": form.cleaned_data.get("name"),
                "admin_no": form.cleaned_data.get("admin_no"),
                "birth_date": form.cleaned_data.get("birth_date"),
                "username": form.cleaned_data.get("username"),
                "password": form.cleaned_data.get("password"),
            }, operator_id=request.user.id)
        else:
            labadmin = update_labadmin(
                labadmin_id=obj.id, 
                validated_data={
                    "name": form.cleaned_data.get("name"),
                    "birth_date": form.cleaned_data.get("birth_date")
                }, operator_id=request.user.id)

        obj.pk = labadmin.pk
        obj.refresh_from_db()

    def delete_model(self, request, obj):
        delete_labadmin(labadmin_id=obj.id, operator_id=request.user.id)

    def delete_queryset(self, request, queryset):
        for labadmin_id in queryset.filter(is_deleted=False).order_by("id").values_list("id", flat=True):
            delete_labadmin(labadmin_id=labadmin_id, operator_id=request.user.id)
            
    def has_delete_permission(self, request, obj = None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj = ...):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj = ...):
        return request.user.is_superuser