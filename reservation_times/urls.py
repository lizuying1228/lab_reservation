from rest_framework.routers import DefaultRouter
from reservation_times.views import ReservationTimeViewSet

router = DefaultRouter()
router.register(
    r"",
    ReservationTimeViewSet,
    basename="reservationtime"
)

urlpatterns = router.urls