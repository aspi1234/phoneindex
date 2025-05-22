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

# monprojet/monprojet/urls.py (Votre urls.py principal)

# home/urls.py
# phoneindex/urls.py
# This is the main URL configuration for your entire Django project.

from django.contrib import admin
from django.urls import path, include
# from django.views.generic import RedirectView # You might not need this if not used

# The problematic line would likely be here or similar:
# from . import views  # <--- THIS IS THE LINE YOU LIKELY NEED TO REMOVE FROM phoneindex/urls.py
# OR
# from phoneindex import views # <--- ALSO WRONG FOR THIS FILE
# OR
# from phoneindex.views import some_view # <--- ALSO WRONG FOR THIS FILE

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), # Includes URLs for user authentication

    # This line correctly includes the URLs from your 'home' app at the project's root.
    # It points to your `home/urls.py` file, which is correct.
    path('', include('home.urls')),

    path('devices/', include('devices.urls', namespace='devices')), # Includes URLs for devices app with a namespace
]

# Don't forget to add static/media files configuration if needed (often for DEBUG mode)
# from django.conf import settings
# from django.conf.urls.static import static
# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)