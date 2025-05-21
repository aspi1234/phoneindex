from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class UserSignUpForm(UserCreationForm):
    # Add any additional fields here that are not on CustomUser directly
    # but needed for signup, or to override widgets/labels.
    # For now, we will just use the fields from the model.

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number')
        # You can customize widgets or labels here if needed, e.g.:
        # widgets = {
        #     'phone_number': forms.TextInput(attrs={'placeholder': 'e.g., +1234567890'}),
        # }
        # help_texts = {
        #     'phone_number': _('Optional: Enter your phone number including country code.'),
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # You can add Bootstrap classes to form fields here if you want
        # For example, to add 'form-control' class to all fields:
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'phone_number': # Example: add placeholder
                 field.widget.attrs['placeholder'] = 'e.g., +237 XXXXXXX'
            # You might want to handle password fields differently if they need specific classes
            # or if UserCreationForm already adds them.
            # UserCreationForm handles password1 and password2 fields.
        
        # Specifically for password fields from UserCreationForm
        if 'password' in self.fields: # Should be password1 from UserCreationForm
            self.fields['password'].widget.attrs['class'] = 'form-control'
        if 'password2' in self.fields: # Confirmation field
            self.fields['password2'].widget.attrs['class'] = 'form-control'


class UserLoginForm(AuthenticationForm):
    # AuthenticationForm expects 'username' by default.
    # Since our CustomUser uses 'email' as USERNAME_FIELD, AuthenticationForm
    # should adapt. If it doesn't, we might need to customize the username field.
    # Let's test it first. AuthenticationForm is generally good at this.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Email Address'
        self.fields['username'].label = 'Email' # Change label from "Username"
        
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['placeholder'] = 'Password'


# forms.py

# --- Summary of Django Form Widgets & Customization ---
#
# What are Widgets?
#   Widgets are Django's mechanism for rendering a form field as HTML
#   (e.g., <input type="text">, <select>, <textarea>) and for extracting
#   raw submitted data for that field from the request. They bridge the
#   logical Field (data type, validation) with its visual representation.
#
# Why customize Widgets?
#   1. Change HTML element type (e.g., CharField as Textarea instead of TextInput).
#   2. Add HTML attributes (e.g., class, id, placeholder, style).
#   3. Integrate with frontend frameworks (e.g., adding Bootstrap classes).
#   4. Use specialized widgets (e.g., date pickers, rich text editors).
#
# How to customize Widgets:
#   1. `Meta.widgets` attribute (in the form's Meta class):
#      - Declarative: Define widget instances for specific fields.
#      - Use: Good for setting the widget type or static attributes
#             that apply when the form class is defined.
#      - Example: `widgets = {'my_field': forms.Textarea(attrs={'rows': 3})}`
#
#   2. In the form's `__init__` method:
#      - Dynamic/Programmatic: Modify `self.fields[field_name].widget.attrs`
#                              after the form instance is created.
#      - Use: Good for applying attributes to many/all fields (e.g., looping),
#             conditional styling, or modifying widgets based on form arguments.
#             Can override or add to attributes set in `Meta.widgets`.
#      - Example:
#        def __init__(self, *args, **kwargs):
#            super().__init__(*args, **kwargs)
#            for field in self.fields.values():
#                field.widget.attrs['class'] = 'form-control'
#
# In this file:
#   - `UserSignUpForm` and `UserLoginForm` use the `__init__` method
#     primarily to dynamically add Bootstrap's 'form-control' class to all
#     fields for consistent styling, and to set placeholders or labels.
#     This is more concise for applying a common style than listing all
#     fields in `Meta.widgets`.
# --- End Summary ---