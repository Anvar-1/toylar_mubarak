from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from config import settings
from config.message.views import MessageListAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('message/', MessageListAPIView.as_view()),
    path('chat/', include('config.message.urls')),
    path('', include('config.account.urls')),
    path('', include('config.profiles.urls')),
    path('', include('config.message.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = [
    path('admin/', admin.site.urls),
]
