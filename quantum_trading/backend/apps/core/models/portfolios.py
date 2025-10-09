# apps/core/models/portfolios.py
class Portfolio(models.Model):
    """
    User portfolio management
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portfolio'
        unique_together = ['user', 'name']

class Position(models.Model):
    """
    Track open and closed positions
    """
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='positions')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    signal = models.ForeignKey(TradingSignal, on_delete=models.SET_NULL, null=True)

    # Position Details
    position_type = models.CharField(max_length=10, choices=[('LONG', 'Long'), ('SHORT', 'Short')])
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    entry_price = models.DecimalField(max_digits=15, decimal_places=6)
    current_price = models.DecimalField(max_digits=15, decimal_places=6, null=True)

    # Exit Conditions
    exit_price = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    stop_loss = models.DecimalField(max_digits=15, decimal_places=6, null=True)
    take_profit = models.DecimalField(max_digits=15, decimal_places=6, null=True)

    # Status
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
        ('PENDING', 'Pending'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True)

    # Performance
    unrealized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    realized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = 'position'
        indexes = [
            models.Index(fields=['portfolio', 'status']),
            models.Index(fields=['asset', 'opened_at']),
        ]

class Trade(models.Model):
    """
    Audit trail for all executed trades
    """
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='trades')
    signal = models.ForeignKey(TradingSignal, on_delete=models.SET_NULL, null=True)

    TRADE_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    price = models.DecimalField(max_digits=15, decimal_places=6)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    executed_at = models.DateTimeField(auto_now_add=True)
    broker_reference = models.CharField(max_length=100, blank=True)  # External broker ID

    class Meta:
        db_table = 'trade'
        indexes = [
            models.Index(fields=['position', 'executed_at']),
        ]