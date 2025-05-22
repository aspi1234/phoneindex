"""
URL configuration for phoneindex project.

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
# your_project_name/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView # Make sure this is imported

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), # This is for your /accounts/signup, /accounts/login etc.
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('home/', RedirectView.as_view(url='/', permanent=True)), # Redirects /home/ to /
    path('devices/', include('devices.urls', namespace='devices')), # Include the namespace here as well
    path('about-us/', TemplateView.as_view(template_name='about_us.html'), name='about_us'),
]
