# apps/prediction/forms.py
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import QuantumEngineConfig

class QuantumEngineConfigForm(forms.ModelForm):
    """
    Form for configuring quantum engine parameters
    Based on your Streamlit sidebar parameters
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Configuration Name'
        })
    )

    # Base Parameters (from your Streamlit sidebar)
    base_window_size = forms.IntegerField(
        label="Base Window Size",
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '10',
            'max': '50',
            'help_text': 'Base window size for MA-DFA calculation (10-50)'
        })
    )
    particle_count = forms.IntegerField(
        label="Particle Count",
        validators=[MinValueValidator(50), MaxValueValidator(500)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '50',
            'max': '500',
            'help_text': 'Number of particles for particle filter (50-500)'
        })
    )
    hurst_threshold = forms.FloatField(
        label="Hurst Threshold",
        validators=[MinValueValidator(0.5), MaxValueValidator(0.8)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.5',
            'max': '0.8',
            'step': '0.01',
            'help_text': 'Base Hurst threshold for regime detection (0.5-0.8)'
        })
    )

    # Advanced Quantum Parameters
    volatility_entropy_weight = forms.FloatField(
        required=False,
        initial=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'help_text': 'Weight for volatility entropy in adaptive window calculation'
        })
    )
    fractal_dimension_weight = forms.FloatField(
        required=False,
        initial=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'help_text': 'Weight for fractal dimension in adaptive window calculation'
        })
    )
    quantum_chaos_parameter = forms.FloatField(
        required=False,
        initial=4.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'help_text': 'Logistic map parameter for chaos optimization'
        })
    )
    learning_rate = forms.FloatField(
        required=False,
        initial=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.001',
            'help_text': 'Learning rate for quantum chaos optimization'
        })
    )

    # Trading Strategy Parameters
    volatility_threshold_quantile = forms.FloatField(
        required=False,
        initial=0.75,
        validators=[MinValueValidator(0.5), MaxValueValidator(0.95)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.5',
            'max': '0.95',
            'step': '0.05',
            'help_text': 'Quantile for volatility threshold in trading strategy'
        })
    )
    fpn_confidence_threshold = forms.FloatField(
        required=False,
        initial=0.7,
        validators=[MinValueValidator(0.5), MaxValueValidator(0.95)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.5',
            'max': '0.95',
            'step': '0.05',
            'help_text': 'Confidence threshold for FPN-DRL signals'
        })
    )

    # Activation
    is_active = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = QuantumEngineConfig
        fields = '__all__'
        exclude = ['created_at', 'updated_at']

    def clean(self):
        cleaned_data = super().clean()

        # Validate that only one configuration can be active
        is_active = cleaned_data.get('is_active')
        if is_active:
            existing_active = QuantumEngineConfig.objects.filter(is_active=True)
            if self.instance:
                existing_active = existing_active.exclude(pk=self.instance.pk)
            if existing_active.exists():
                raise forms.ValidationError(
                    "Another configuration is already active. Only one configuration can be active at a time."
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Ensure parameters are within valid ranges
        instance.base_window_size = max(10, min(50, instance.base_window_size))
        instance.particle_count = max(50, min(500, instance.particle_count))
        instance.hurst_threshold = max(0.5, min(0.8, instance.hurst_threshold))

        if commit:
            instance.save()

        return instance

class AnalysisRequestForm(forms.Form):
    """
    Form for requesting quantum analysis on specific assets
    """
    symbol = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., AAPL, TSLA, BTC-USD',
            'list': 'asset-suggestions'
        })
    )
    engine_config = forms.ModelChoiceField(
        queryset=QuantumEngineConfig.objects.filter(is_active=True),
        empty_label="Use Active Configuration",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    timeframe = forms.ChoiceField(
        choices=[
            ('1D', 'Daily'),
            ('1H', 'Hourly'),
            ('4H', '4-Hour'),
            ('1W', 'Weekly'),
        ],
        initial='1D',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    include_technical_analysis = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    generate_trading_signal = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_symbol(self):
        symbol = self.cleaned_data.get('symbol').upper().strip()
        if not symbol:
            raise forms.ValidationError("Symbol is required.")

        # Basic validation for symbol format
        if len(symbol) < 1 or len(symbol) > 20:
            raise forms.ValidationError("Symbol must be between 1 and 20 characters.")

        return symbol

class SignalFilterForm(forms.Form):
    """
    Form for filtering trading signals
    """
    SIGNAL_CHOICES = [
        ('', 'All Signals'),
        ('BUY', 'Buy Signals'),
        ('SELL', 'Sell Signals'),
        ('HOLD', 'Hold Signals'),
    ]

    CONFIDENCE_CHOICES = [
        ('', 'Any Confidence'),
        ('high', 'High Confidence (>0.7)'),
        ('medium', 'Medium Confidence (0.5-0.7)'),
        ('low', 'Low Confidence (<0.5)'),
    ]

    signal_type = forms.ChoiceField(
        choices=SIGNAL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    confidence_level = forms.ChoiceField(
        choices=CONFIDENCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    asset_symbol = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by symbol...'
        })
    )
    date_range = forms.ChoiceField(
        choices=[
            ('', 'Any Time'),
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    engine_config = forms.ModelChoiceField(
        queryset=QuantumEngineConfig.objects.all(),
        required=False,
        empty_label="All Configurations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )