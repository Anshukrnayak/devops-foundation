# apps/core/forms.py
from django import forms
from core.models.market_data import Asset

class AssetSearchForm(forms.Form):
    """
    Form for searching assets
    """
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by symbol or name...',
            'id': 'asset-search'
        })
    )
    asset_type = forms.ChoiceField(
        choices=[
            ('', 'All Types'),
            ('STOCK', 'Stocks'),
            ('CRYPTO', 'Cryptocurrency'),
            ('FOREX', 'Forex'),
            ('ETF', 'ETF'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    exchange = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by exchange...'
        })
    )

class WatchlistForm(forms.Form):
    """
    Form for managing watchlists
    """
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    symbols = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter symbols separated by commas',
            'rows': 3
        })
    )
    is_public = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_symbols(self):
        symbols = self.cleaned_data.get('symbols')
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            # Validate symbols exist
            existing_symbols = Asset.objects.filter(
                symbol__in=symbol_list, is_active=True
            ).values_list('symbol', flat=True)

            invalid_symbols = set(symbol_list) - set(existing_symbols)
            if invalid_symbols:
                raise forms.ValidationError(
                    f"Invalid symbols: {', '.join(invalid_symbols)}"
                )

            return symbol_list
        return []

class MarketDataExportForm(forms.Form):
    """
    Form for exporting market data
    """
    symbol = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    data_type = forms.ChoiceField(
        choices=[
            ('OHLC', 'OHLC Data'),
            ('INDICATORS', 'Technical Indicators'),
            ('PREDICTIONS', 'Prediction Data'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    format = forms.ChoiceField(
        choices=[
            ('CSV', 'CSV'),
            ('JSON', 'JSON'),
            ('EXCEL', 'Excel'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date cannot be after end date.")

        return cleaned_data