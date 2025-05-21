from django.urls import path
from .views import SignUpView, UserLoginView, user_logout_view

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', user_logout_view, name='logout'),
]