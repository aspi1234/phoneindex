
# home/urls.py
from django.urls import path
from . import views # Importer les vues de votre application home

app_name = 'home' # TRÈS IMPORTANT : Définit le namespace de l'application

urlpatterns = [
    path('', views.home_view, name='home'), # Assurez-vous d'avoir une vue 'home_view' dans home/views.py
                                            # pour la page d'accueil.
    path('about-us/', views.about_us_view, name='about_us'), # Votre URL pour About Us
    # ... d'autres URLs de votre application home
]




