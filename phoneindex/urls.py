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

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView # TemplateView n'est plus nécessaire ici pour la page d'accueil

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), # Ceci est pour vos /accounts/signup, /accounts/login etc.

    # --- MODIFICATION ICI ---
    # Incluez les URLs de votre application 'home' à la racine du site.
    # Assurez-vous que votre application 'home' a un fichier urls.py
    # et que ce fichier définit 'app_name = "home"' et une URL nommée 'home'
    # pour votre page d'accueil, et 'about_us' pour la page About Us.
    path('', include('home.urls')),
    # --- FIN MODIFICATION ---

    # Cette ligne n'est plus nécessaire si votre home.urls gère la racine
    # path('home/', RedirectView.as_view(url='/', permanent=True)),

    path('devices/', include('devices.urls', namespace='devices')), # Inclure le namespace ici aussi
]

# N'oubliez pas d'ajouter les configurations pour les fichiers statiques/médias si vous en avez besoin
# (souvent ajoutées à la fin du fichier urls.py principal en mode DEBUG)
# from django.conf import settings
# from django.conf.urls.static import static
# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)