from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm, UserChangeForm as BaseUserChangeForm
from .models import CustomUser
from django import forms # For potential widget customization if needed

# Custom UserCreationForm for the admin "add user" page
class CustomUserAdminCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = CustomUser
        # Fields that will appear on the "add user" form.
        # 'email' is our USERNAME_FIELD.
        # 'password' and 'password2' (confirmation) are handled by BaseUserCreationForm.
        fields = ('email', 'first_name', 'last_name', 'phone_number')

# Custom UserChangeForm for the admin "change user" page
class CustomUserAdminChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = CustomUser
        # Fields that will appear on the "change user" form.
        # '__all__' includes all model fields.
        # Or, be explicit:
        fields = ('email', 'first_name', 'last_name', 'phone_number', 
                  'is_active', 'is_staff', 'is_superuser', 
                  'groups', 'user_permissions') 
        # Password is handled differently in UserChangeForm (usually a link to a separate change password form)


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserAdminChangeForm
    add_form = CustomUserAdminCreationForm

    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)

    # Fieldsets for the "change user" page
    # BaseUserAdmin.fieldsets already includes 'username'. We need to ensure it uses 'email'.
    # And we need to add 'phone_number'.
    # The BaseUserAdmin is usually smart enough to use USERNAME_FIELD.
    # Let's inspect default fieldsets and adapt.
    # Default UserAdmin fieldsets:
    # (None, {'fields': ('username', 'password')}),
    # ('Personal info', {'fields': ('first_name', 'last_name', 'email')}), # Note: email is here by default too
    # ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    # ('Important dates', {'fields': ('last_login', 'date_joined')}),

    # Our Customization:
    fieldsets = (
        (None, {'fields': ('email', 'password')}), # 'email' is our USERNAME_FIELD
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}), # Added 'phone_number'
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Fieldsets for the "add user" page.
    # These fields come from `add_form` (CustomUserAdminCreationForm).
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'password', 'password2'),
        }),
    )