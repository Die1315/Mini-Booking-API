from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from bookings.views import GoogleLogin, google_callback

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('bookings.urls')),
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('google/callback/', google_callback, name='google_callback'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
