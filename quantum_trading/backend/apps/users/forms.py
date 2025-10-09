# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import EmailValidator, MinLengthValidator
from .models import CustomUser, UserProfile

class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form with email as username
    """
    email = forms.EmailField(
        max_length=255,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    risk_profile = forms.ChoiceField(
        choices=CustomUser.RISK_PROFILE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    trading_experience = forms.IntegerField(
        min_value=0,
        max_value=50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Years of trading experience'
        })
    )
    initial_capital = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Initial capital ($)'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2',
                  'risk_profile', 'trading_experience', 'initial_capital')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Use email as username
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """
    User profile update form
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'risk_profile',
                  'trading_experience', 'email_notifications', 'sms_notifications', 'dark_mode')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values from user instance
        if self.instance:
            self.fields['email'].initial = self.instance.email
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name

class UserPreferencesForm(forms.ModelForm):
    """
    Trading preferences and risk management form
    """
    max_position_size = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=100,
        max_value=100000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'help_text': 'Maximum amount to invest in a single position'
        })
    )
    max_daily_loss = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=10,
        max_value=5000,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'help_text': 'Maximum allowed loss per day'
        })
    )
    max_portfolio_risk = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0.1,
        max_value=10.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'help_text': 'Maximum portfolio risk percentage'
        })
    )
    default_timeframe = forms.ChoiceField(
        choices=[
            ('1H', '1 Hour'),
            ('4H', '4 Hours'),
            ('1D', '1 Day'),
            ('1W', '1 Week'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = ('max_position_size', 'max_daily_loss', 'max_portfolio_risk',
                  'default_timeframe', 'favorite_tickers')

    def clean_max_daily_loss(self):
        max_daily_loss = self.cleaned_data.get('max_daily_loss')
        max_position_size = self.cleaned_data.get('max_position_size')

        if max_daily_loss and max_position_size:
            if max_daily_loss > max_position_size:
                raise forms.ValidationError(
                    "Daily loss limit cannot exceed maximum position size."
                )

        return max_daily_loss

class BrokerConnectionForm(forms.Form):
    """
    Form for connecting brokerage accounts
    """
    BROKER_CHOICES = [
        ('ALPACA', 'Alpaca'),
        ('IBKR', 'Interactive Brokers'),
        ('TD_AMERITRADE', 'TD Ameritrade'),
    ]

    broker = forms.ChoiceField(
        choices=BROKER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    api_key = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'API Key'
        })
    )
    secret_key = forms.CharField(
        max_length=255,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Secret Key'
        })
    )
    paper_trading = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        # Add broker-specific validation here
        return cleaned_data