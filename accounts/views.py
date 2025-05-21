from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView as BaseLoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import UserSignUpForm, UserLoginForm
from django.contrib import messages # For displaying messages to the user

# --- User Registration (Sign Up) ---
class SignUpView(CreateView):
    form_class = UserSignUpForm
    template_name = 'accounts/signup.html' # We'll create this template next
    success_url = reverse_lazy('login') # Redirect to login page after successful registration

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        response = super().form_valid(form)
        # Optionally, log the user in directly after registration
        # user = form.save() # form.save() is already called by super().form_valid(form)
        # login(self.request, self.object) # self.object is the created user instance
        
        # Add a success message
        messages.success(self.request, f"Account created for {self.object.email}! You can now log in.")
        # The success_url will handle the redirect.
        return response

    def form_invalid(self, form):
        # Add a message for an invalid form
        messages.error(self.request, "There was an error with your registration. Please check the details provided.")
        return super().form_invalid(form)


# --- User Login ---
# We can use Django's built-in LoginView and customize it slightly if needed,
# or write our own function-based view for more control.
# Using Django's built-in LoginView is often cleaner.

class UserLoginView(BaseLoginView):
    form_class = UserLoginForm # Use our custom form
    template_name = 'accounts/login.html' # We'll create this template next
    # success_url is handled by LOGIN_REDIRECT_URL in settings.py by default
    # Or you can set it here: success_url = reverse_lazy('some_dashboard_page')

    def form_valid(self, form):
        # Called when the form is valid (user is authenticated)
        messages.success(self.request, f"Welcome back, {form.get_user().first_name or form.get_user().email}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        # Called when the form is invalid (e.g., wrong credentials)
        messages.error(self.request, "Invalid email or password. Please try again.")
        return super().form_invalid(form)


# --- User Logout ---
def user_logout_view(request):
    if request.user.is_authenticated:
        # Get user's name before logging out for the message
        user_name = request.user.first_name or request.user.email
        logout(request)
        messages.info(request, f"You have been successfully logged out, {user_name}.")
    else:
        messages.info(request, "You were not logged in.")
    return redirect('login') # Redirect to login page or homepage after logout
                            # Consider LOGOUT_REDIRECT_URL from settings.py
                            # Or specify a URL name: redirect(reverse_lazy('home'))