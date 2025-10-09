# apps/core/models/market_data.py
class Asset(models.Model):
    """
    Master table for all tradable assets
    """
    symbol = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=50)  # STOCK, CRYPTO, FOREX, etc.
    currency = models.CharField(max_length=10, default='USD')
    exchange = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

    # Metadata
    sector = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'asset'
        indexes = [
            models.Index(fields=['symbol', 'is_active']),
            models.Index(fields=['asset_type']),
        ]

class MarketData(models.Model):
    """
    Time-series market data with partitioning support
    """
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='market_data')
    timestamp = models.DateTimeField(db_index=True)
    open = models.DecimalField(max_digits=15, decimal_places=6)
    high = models.DecimalField(max_digits=15, decimal_places=6)
    low = models.DecimalField(max_digits=15, decimal_places=6)
    close = models.DecimalField(max_digits=15, decimal_places=6)
    volume = models.BigIntegerField()

    # Derived fields for performance
    returns = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    volatility = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'market_data'
        unique_together = ['asset', 'timestamp']
        indexes = [
            models.Index(fields=['asset', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

class TechnicalIndicator(models.Model):
    """
    Store pre-calculated technical indicators for performance
    """
    market_data = models.ForeignKey(MarketData, on_delete=models.CASCADE, related_name='indicators')

    # Your Quantum Indicators
    hurst_exponent = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    hurst_up = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    hurst_down = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    particle_volatility = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    hurst_threshold = models.DecimalField(max_digits=10, decimal_places=6, null=True)

    # Traditional Indicators
    rsi = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    macd = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    bollinger_upper = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    bollinger_lower = models.DecimalField(max_digits=15, decimal_places=6, null=True)

    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'technical_indicator'
        indexes = [
            models.Index(fields=['market_data']),
        ]