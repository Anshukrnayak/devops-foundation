# apps/users/managers.py
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
import re

class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser with email authentication
    Enhanced with trading-specific validation
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password
        """
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        self._validate_trading_profile(extra_fields)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

    def _validate_trading_profile(self, extra_fields):
        """Validate trading-specific fields during user creation"""
        risk_profile = extra_fields.get('risk_profile', 'MODERATE')
        if risk_profile not in dict(CustomUser.RISK_PROFILE_CHOICES):
            raise ValidationError('Invalid risk profile')