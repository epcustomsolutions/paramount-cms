from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.app_home, name='app-home'),
    path('schedule/', include('scheduling.urls')),
    path('clients/', include('clients.urls')),
    path('claims/', include('claims.urls')),
    path('tools/', include('tools.urls')),
    path('healthz/', views.healthz, name='healthz'),
]

