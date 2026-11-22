from django.contrib import admin
from students.models import Student
from django import forms
from students.services import create_student, delete_student, update_student

# Register your models here.
class StudentCreateAdminForm(forms.ModelForm):
    user_id = forms.IntegerField(required=False, min_value=1, label="已有用户ID", help_text="绑定已有用户时填写，创建新用户留空")
    username = forms.CharField(required=False, max_length=150, label="用户名")
    password = forms.CharField(required=False, min_length=8, label="密码", widget=forms.PasswordInput)

    class Meta:
        model = Student
        fields = ["name", "student_no", "birth_date"]

    def clean(self):
        cleaned_data = super().clean()

        user_id = cleaned_data.get("user_id")
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if user_id is not None:
            if username or password:
                raise forms.ValidationError("绑定已有用户ID时，不允许新建用户")

        else:
            if not username or not password:
                raise forms.ValidationError("新建用户时必须有用户名和密码")

        return cleaned_data


class StudentUpdateAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["name", "birth_date"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["name", "student_no", "birth_date", "user", "is_deleted"]
    search_fields = ["name", "student_no"]
    list_filter = ["is_deleted"]
    ordering = ["student_no"]

    def get_readonly_fields(self, request, obj = ...):
        if obj is None:
            return ["is_deleted", "deleted_at"]
        return ["student_no", "user", "is_deleted", "deleted_at"]

    def get_form(self, request, obj = None, **kwargs):
        if obj is None:
            kwargs["form"] = StudentCreateAdminForm
        else:
            kwargs["form"] = StudentUpdateAdminForm

        return super().get_form(request, obj, **kwargs)

    def get_fields(self, request, obj = ...):
        if obj is None:
            return ["name", "student_no", "birth_date", "user_id", "username", "password"]
        return ["name", "student_no", "birth_date", "user", "is_deleted", "deleted_at"]

    def save_model(self, request, obj, form, change):
        if not change:
            student = create_student(validated_data={
                "name": form.cleaned_data.get("name"),
                "student_no": form.cleaned_data.get("student_no"),
                "birth_date": form.cleaned_data.get("birth_date"),
                "user_id": form.cleaned_data.get("user_id"),
                "username": form.cleaned_data.get("username"),
                "password": form.cleaned_data.get("password"),
            }, operator_id=request.user.id)
        else:
            student = update_student(
                student_id=obj.id,
                validated_data={
                    "name": form.cleaned_data.get("name"),
                    "birth_date": form.cleaned_data.get("birth_date")
                },
                operator_id=request.user.id
            )

        obj.pk = student.pk
        obj.refresh_from_db()

    def delete_model(self, request, obj):
        delete_student(
            student_id=obj.id,
            operator_id=request.user.id
        )

    def delete_queryset(self, request, queryset):
        for student_id in queryset.filter(is_deleted=False).order_by("id").values_list("id", flat=True):
            delete_student(
                student_id=student_id,
                operator_id=request.user.id
            )
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj = None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return request.user.is_superuser