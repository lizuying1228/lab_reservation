from rest_framework.routers import DefaultRouter
from labs.views import LabViewSet

router = DefaultRouter()
router.register(
    r"",
    LabViewSet,
    basename="lab"
)

urlpatterns = router.urls