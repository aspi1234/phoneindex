# home/views.py
from django.shortcuts import render

def home_view(request):
    """
    Renders the main homepage (home.html).
    This view will be linked to the root URL (/).
    """
    return render(request, 'home.html')

def about_us_view(request):
    """
    Renders the About Us page (about_us.html).
    This view will be linked to the /about-us/ URL.
    """
    return render(request, 'about_us.html')

# Si 'homepage_view' et 'nav.html' sont des restes d'anciens essais,
# vous pouvez les supprimer complètement.
# Si 'nav.html' est une vue spécifique pour une autre partie du site,
# elle devrait avoir sa propre URL dédiée et ne pas être mélangée
# avec la logique de la page d'accueil ici.