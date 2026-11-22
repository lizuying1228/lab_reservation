from rest_framework.routers import DefaultRouter
from lab_admins.views import LabAdminViewSet

router = DefaultRouter()
router.register(
    r"",
    LabAdminViewSet,
    basename="labadmin"
)

urlpatterns = router.urls