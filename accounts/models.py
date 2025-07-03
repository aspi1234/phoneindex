from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    # We don't need a username, AbstractUser provides it, but we'll ignore it
    # by setting USERNAME_FIELD to 'email'.
    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    
    # Add our custom fields
    # 'name' from the user story will be split into first_name and last_name
    # first_name and last_name are already part of AbstractUser
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True,null=True) # Making blank=True initially, can be changed

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name'] # email and password are required by default.

    objects = CustomUserManager() # assigning the manager

    def __str__(self):
        return self.email