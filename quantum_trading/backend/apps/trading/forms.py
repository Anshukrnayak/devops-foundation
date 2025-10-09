# apps/trading/forms.py
from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import Order, TradingAccount
from core.models.market_data import Asset

class OrderForm(forms.ModelForm):
    """
    Form for placing trading orders
    """
    symbol = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter symbol (e.g., AAPL)',
            'id': 'order-symbol'
        })
    )
    trading_account = forms.ModelChoiceField(
        queryset=TradingAccount.objects.none(),  # Will be set in __init__
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.DecimalField(
        max_digits=15,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0.000001'))],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.000001',
            'placeholder': 'Quantity'
        })
    )
    limit_price = forms.DecimalField(
        max_digits=15,
        decimal_places=6,
        required=False,
        validators=[MinValueValidator(Decimal('0.01'))],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Limit Price (optional for market orders)'
        })
    )
    stop_price = forms.DecimalField(
        max_digits=15,
        decimal_places=6,
        required=False,
        validators=[MinValueValidator(Decimal('0.01'))],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Stop Price (for stop orders)'
        })
    )

    class Meta:
        model = Order
        fields = ['trading_account', 'order_type', 'side', 'time_in_force',
                  'quantity', 'limit_price', 'stop_price']
        widgets = {
            'order_type': forms.Select(attrs={'class': 'form-control'}),
            'side': forms.Select(attrs={'class': 'form-control'}),
            'time_in_force': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Set trading account choices for this user
        self.fields['trading_account'].queryset = TradingAccount.objects.filter(
            user=user, is_active=True
        )

        # Add dynamic help text
        self.fields['limit_price'].help_text = "Required for limit orders"
        self.fields['stop_price'].help_text = "Required for stop orders"

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('order_type')
        limit_price = cleaned_data.get('limit_price')
        stop_price = cleaned_data.get('stop_price')
        symbol = cleaned_data.get('symbol')

        # Validate symbol exists
        if symbol:
            try:
                asset = Asset.objects.get(symbol=symbol.upper(), is_active=True)
                cleaned_data['asset'] = asset
            except Asset.DoesNotExist:
                raise forms.ValidationError(f"Asset {symbol} not found or not active.")

        # Validate order type requirements
        if order_type == 'LIMIT' and not limit_price:
            raise forms.ValidationError("Limit price is required for limit orders.")

        if order_type in ['STOP', 'STOP_LIMIT'] and not stop_price:
            raise forms.ValidationError("Stop price is required for stop orders.")

        if order_type == 'STOP_LIMIT' and not limit_price:
            raise forms.ValidationError("Limit price is required for stop-limit orders.")

        # Validate price relationships
        if limit_price and stop_price:
            if order_type == 'STOP_LIMIT' and stop_price >= limit_price:
                raise forms.ValidationError(
                    "For stop-limit orders, stop price must be less than limit price."
                )

        return cleaned_data

    def save(self, commit=True):
        # This form doesn't save directly - it's used for validation
        # The actual saving happens in the view
        return self.cleaned_data

class QuickOrderForm(forms.Form):
    """
    Simplified form for quick trading
    """
    symbol = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'SYMBOL'
        })
    )
    action = forms.ChoiceField(
        choices=[('BUY', 'Buy'), ('SELL', 'Sell')],
        widget=forms.RadioSelect(attrs={'class': 'btn-check'})
    )
    quantity_type = forms.ChoiceField(
        choices=[('shares', 'Shares'), ('dollars', 'Dollars')],
        initial='shares',
        widget=forms.RadioSelect(attrs={'class': 'btn-check'})
    )
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Amount'
        })
    )
    order_type = forms.ChoiceField(
        choices=[('MARKET', 'Market'), ('LIMIT', 'Limit')],
        initial='MARKET',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        symbol = cleaned_data.get('symbol')

        if symbol:
            # Validate symbol exists
            try:
                Asset.objects.get(symbol=symbol.upper(), is_active=True)
            except Asset.DoesNotExist:
                raise forms.ValidationError(f"Asset {symbol} not found.")

        return cleaned_data

class PortfolioAllocationForm(forms.Form):
    """
    Form for portfolio allocation and rebalancing
    """
    target_allocation = forms.JSONField(
        widget=forms.HiddenInput()  # Will be handled by JavaScript
    )
    rebalance_threshold = forms.FloatField(
        initial=5.0,
        min_value=1.0,
        max_value=20.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'help_text': 'Percentage threshold for triggering rebalance'
        })
    )
    execute_immediately = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class TradingStrategyForm(forms.Form):
    """
    Form for configuring automated trading strategies
    """
    STRATEGY_CHOICES = [
        ('QUANTUM_SIGNALS', 'Quantum Signal Following'),
        ('MEAN_REVERSION', 'Mean Reversion'),
        ('TREND_FOLLOWING', 'Trend Following'),
    ]

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    strategy_type = forms.ChoiceField(
        choices=STRATEGY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    enabled = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # Quantum Strategy Specific
    min_confidence = forms.FloatField(
        initial=0.7,
        min_value=0.5,
        max_value=0.95,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.05'
        })
    )
    position_size_percent = forms.FloatField(
        initial=2.0,
        min_value=0.1,
        max_value=10.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'help_text': 'Percentage of portfolio per trade'
        })
    )

    # Risk Management
    max_positions = forms.IntegerField(
        initial=10,
        min_value=1,
        max_value=50,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    stop_loss_percent = forms.FloatField(
        initial=5.0,
        min_value=1.0,
        max_value=20.0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    take_profit_percent = forms.FloatField(
        initial=10.0,
        min_value=2.0,
        max_value=50.0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        stop_loss = cleaned_data.get('stop_loss_percent')
        take_profit = cleaned_data.get('take_profit_percent')

        if stop_loss and take_profit and take_profit <= stop_loss:
            raise forms.ValidationError(
                "Take profit percentage must be greater than stop loss percentage."
            )

        return cleaned_data