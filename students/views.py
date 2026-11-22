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
        user = self.request.user
        delete_student(student_id=instance.id, user_id=user.id)


    