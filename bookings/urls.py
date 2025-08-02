from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookingViewSet, LoginView, RegisterView

router = DefaultRouter()
router.register(r'bookings', BookingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),

]
