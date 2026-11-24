from rest_framework.viewsets import ModelViewSet
from students.models import Student
from students.serializers import StudentCreateSerializer, StudentSerializer
from students.permissions import StudentPermission
from students.services import delete_student
import logging

logger = logging.getLogger(__name__)

# Create your views here.
class StudentViewSet(ModelViewSet):
    permission_classes = [StudentPermission]
    filterset_fields = ["student_no", "name"]
    search_fields = ["name", "student_no", "user__username"]
    ordering_fields = ["id", "name", "student_no", "birth_date"]
    ordering = ["id"]

    def get_serializer_class(self):
        if self.action == "create":
            return StudentCreateSerializer
        return StudentSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or hasattr(user, "labadmin"):
            return Student.objects.filter(is_deleted=False).select_related("user")
        
        elif hasattr(user, "student"):
            return Student.objects.filter(user=user, is_deleted=False).select_related("user")
        
        return Student.objects.none()

    def perform_destroy(self, instance):
        operator_id = self.request.user.id
        delete_student(student_id=instance.id, operator_id=operator_id)


    