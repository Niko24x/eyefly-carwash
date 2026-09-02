"""
URL configuration for carwash project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic.base import RedirectView

from accounts.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'favicon.ico',
        RedirectView.as_view(
            url=static_url('images/brand/favicon.png'),
            permanent=False,
        ),
    ),
    path('dashboard/', include('dashboard.urls')),
    path('configuracion/', include('configuracion.urls')),
    path('edificios/', include('edificios.urls')),
    path('servicios/', include('servicios.urls')),
    path('notificaciones/', include('notificaciones.urls')),
    path('', include('appointments.urls')),
    path('cuentas/', include('accounts.urls')),
    path(
        'cuentas/login/',
        auth_views.LoginView.as_view(
            authentication_form=LoginForm,
            template_name='registration/login.html',
        ),
        name='login',
    ),
    path('cuentas/logout/', auth_views.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
