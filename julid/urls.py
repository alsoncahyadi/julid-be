"""julid URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.views.decorators.csrf import csrf_exempt
from django.urls import include, path
from django.contrib import admin
from rest_framework import routers
from .rest_resources import *
from . import views
import os

router = routers.DefaultRouter()
router.register('complaints', ComplaintViewSet)
router.register('logs', LogViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('trello/', include('trel.urls')),
    path('api/', include(router.urls)),
    # path('rest-auth/login/$', views.LoginViewCustom.as_view(), name='rest_login'),
    # path('rest-auth/', include('rest_auth.urls')),
]
