# apps/users/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import CustomUserManager

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with email as primary identifier
    Enhanced for financial trading system requirements
    """
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)

    # Personal Information
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True, blank=True)

    # Trading Profile
    RISK_PROFILE_CHOICES = [
        ('CONSERVATIVE', 'Conservative'),
        ('MODERATE', 'Moderate'),
        ('AGGRESSIVE', 'Aggressive'),
        ('QUANTUM', 'Quantum'),
    ]
    risk_profile = models.CharField(max_length=20, choices=RISK_PROFILE_CHOICES, default='MODERATE')
    trading_experience = models.PositiveIntegerField(default=0)  # in years
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2, default=10000.00)

    # Account Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)

    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['date_joined']),
        ]

class UserProfile(models.Model):
    """
    Extended user profile for trading-specific data
    Separated for performance optimization
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')

    # Trading Limits
    max_position_size = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    max_daily_loss = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    max_portfolio_risk = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)  # Percentage

    # API Keys (encrypted)
    alpaca_api_key = models.TextField(blank=True)
    alpaca_secret_key = models.TextField(blank=True)

    # Preferences
    default_timeframe = models.CharField(max_length=10, default='1D')
    favorite_tickers = models.JSONField(default=list)  # Store as list of tickers

    class Meta:
        db_table = 'user_profile'