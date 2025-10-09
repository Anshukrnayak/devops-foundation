

# config/urls.py (main)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('prediction/', include('prediction.urls')),
    path('trading/', include('trading.urls')),
    path('users/', include('users.urls')),
]