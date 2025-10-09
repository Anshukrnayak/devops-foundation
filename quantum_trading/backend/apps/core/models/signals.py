# apps/core/models/signals.py
class PredictionEngine(models.Model):
    """
    Track different prediction engines (Quantum, ML, Technical)
    """
    name = models.CharField(max_length=100)
    engine_type = models.CharField(max_length=50)  # QUANTUM, ML, TECHNICAL
    version = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    parameters = models.JSONField(default=dict)  # Engine-specific parameters

    class Meta:
        db_table = 'prediction_engine'

class TradingSignal(models.Model):
    """
    Generated trading signals from prediction engines
    """
    SIGNAL_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
        ('HOLD', 'Hold'),
        ('STRONG_BUY', 'Strong Buy'),
        ('STRONG_SELL', 'Strong Sell'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    prediction_engine = models.ForeignKey(PredictionEngine, on_delete=models.CASCADE)
    signal_type = models.CharField(max_length=20, choices=SIGNAL_TYPES)
    confidence = models.DecimalField(max_digits=5, decimal_places=4)  # 0.0000 to 1.0000

    # Signal Details
    generated_at = models.DateTimeField(auto_now_add=True)
    target_price = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    stop_loss = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    timeframe = models.CharField(max_length=10)  # 1H, 4H, 1D, etc.

    # Quantum-Specific Metrics
    hurst_value = models.DecimalField(max_digits=10, decimal_places=6, null=True)
    volatility_regime = models.CharField(max_length=20, null=True)
    fractal_dimension = models.DecimalField(max_digits=10, decimal_places=6, null=True)

    is_executed = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'trading_signal'
        indexes = [
            models.Index(fields=['asset', 'generated_at']),
            models.Index(fields=['signal_type', 'confidence']),
            models.Index(fields=['expires_at', 'is_executed']),
        ]

class BacktestResult(models.Model):
    """
    Store backtesting results for strategy validation
    """
    prediction_engine = models.ForeignKey(PredictionEngine, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    # Performance Metrics
    total_return = models.DecimalField(max_digits=10, decimal_places=4)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4)
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4)
    win_rate = models.DecimalField(max_digits=10, decimal_places=4)

    # Test Parameters
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2)

    detailed_metrics = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'backtest_result'