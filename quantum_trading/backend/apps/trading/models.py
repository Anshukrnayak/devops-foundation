# apps/trading/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from core.models.market_data import Asset
from core.models.signals import TradingSignal
from users.models import CustomUser
import uuid

class Broker(models.Model):
    """
    Supported brokerage integrations
    """
    BROKER_CHOICES = [
        ('ALPACA', 'Alpaca'),
        ('IBKR', 'Interactive Brokers'),
        ('TD_AMERITRADE', 'TD Ameritrade'),
        ('TRADIER', 'Tradier'),
    ]

    name = models.CharField(max_length=50, choices=BROKER_CHOICES)
    api_key_encrypted = models.TextField(blank=True)
    secret_key_encrypted = models.TextField(blank=True)
    base_url = models.URLField()
    is_active = models.BooleanField(default=True)
    paper_trading = models.BooleanField(default=True)

    # Rate limiting
    requests_per_minute = models.PositiveIntegerField(default=100)
    last_request_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'broker'
        verbose_name = 'Broker'
        verbose_name_plural = 'Brokers'

class TradingAccount(models.Model):
    """
    User's trading account linked to a broker
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='trading_accounts')
    broker = models.ForeignKey(Broker, on_delete=models.CASCADE)
    account_id = models.CharField(max_length=100, help_text="Broker's account ID")

    # Account Details
    account_number = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    is_default = models.BooleanField(default=False)

    # Balance Information
    buying_power = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cash = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    portfolio_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Status
    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trading_account'
        verbose_name = 'Trading Account'
        verbose_name_plural = 'Trading Accounts'
        unique_together = ['user', 'broker', 'account_id']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['last_synced']),
        ]

class Order(models.Model):
    """
    Trading orders with full audit trail
    """
    ORDER_TYPES = [
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
        ('STOP', 'Stop'),
        ('STOP_LIMIT', 'Stop Limit'),
        ('TRAILING_STOP', 'Trailing Stop'),
    ]

    ORDER_SIDES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    ORDER_STATUS = [
        ('PENDING', 'Pending'),
        ('SUBMITTED', 'Submitted'),
        ('PARTIALLY_FILLED', 'Partially Filled'),
        ('FILLED', 'Filled'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]

    TIME_IN_FORCE = [
        ('DAY', 'Day'),
        ('GTC', 'Good Till Cancelled'),
        ('OPG', 'At Opening'),
        ('CLS', 'At Close'),
        ('IOC', 'Immediate or Cancel'),
        ('FOK', 'Fill or Kill'),
    ]

    # Identifiers
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_order_id = models.CharField(max_length=100, unique=True)
    broker_order_id = models.CharField(max_length=100, blank=True, db_index=True)

    # Relationships
    trading_account = models.ForeignKey(TradingAccount, on_delete=models.CASCADE, related_name='orders')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    signal = models.ForeignKey(TradingSignal, on_delete=models.SET_NULL, null=True, blank=True)

    # Order Details
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES)
    side = models.CharField(max_length=10, choices=ORDER_SIDES)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='PENDING')
    time_in_force = models.CharField(max_length=10, choices=TIME_IN_FORCE, default='DAY')

    # Quantity and Price
    quantity = models.DecimalField(max_digits=15, decimal_places=6, validators=[MinValueValidator(0)])
    filled_quantity = models.DecimalField(max_digits=15, decimal_places=6, default=0)

    limit_price = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    stop_price = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    average_fill_price = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)

    # Commission and Fees
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    filled_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Additional Data
    notes = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'order'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['trading_account', 'status']),
            models.Index(fields=['asset', 'created_at']),
            models.Index(fields=['broker_order_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'side']),
        ]
        ordering = ['-created_at']

class Position(models.Model):
    """
    Real-time position tracking (separate from core portfolio models)
    """
    trading_account = models.ForeignKey(TradingAccount, on_delete=models.CASCADE, related_name='positions')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    # Position Details
    quantity = models.DecimalField(max_digits=15, decimal_places=6, default=0)
    average_entry_price = models.DecimalField(max_digits=15, decimal_places=6)
    current_price = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)

    # Calculated Fields
    market_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unrealized_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unrealized_pnl_percent = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    # Status
    is_open = models.BooleanField(default=True)

    # Timestamps
    opened_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'trading_position'
        verbose_name = 'Trading Position'
        verbose_name_plural = 'Trading Positions'
        unique_together = ['trading_account', 'asset', 'is_open']
        indexes = [
            models.Index(fields=['trading_account', 'is_open']),
            models.Index(fields=['asset', 'opened_at']),
        ]

class Trade(models.Model):
    """
    Individual trade executions (fills)
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='trades')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    # Trade Execution Details
    execution_id = models.CharField(max_length=100, unique=True)
    broker_execution_id = models.CharField(max_length=100, blank=True)

    quantity = models.DecimalField(max_digits=15, decimal_places=6)
    price = models.DecimalField(max_digits=15, decimal_places=6)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Timestamps
    executed_at = models.DateTimeField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    # Additional Info
    exchange = models.CharField(max_length=50, blank=True)
    liquidity = models.CharField(max_length=10, choices=[('M', 'Maker'), ('T', 'Taker')], blank=True)

    class Meta:
        db_table = 'trade'
        verbose_name = 'Trade'
        verbose_name_plural = 'Trades'
        indexes = [
            models.Index(fields=['order', 'executed_at']),
            models.Index(fields=['asset', 'executed_at']),
            models.Index(fields=['executed_at']),
        ]
        ordering = ['-executed_at']

class TradingStrategy(models.Model):
    """
    Configurable trading strategies
    """
    STRATEGY_TYPES = [
        ('QUANTUM', 'Quantum-Charged'),
        ('MEAN_REVERSION', 'Mean Reversion'),
        ('TREND_FOLLOWING', 'Trend Following'),
        ('ARBITRAGE', 'Arbitrage'),
        ('ML', 'Machine Learning'),
    ]

    name = models.CharField(max_length=100)
    strategy_type = models.CharField(max_length=20, choices=STRATEGY_TYPES)
    description = models.TextField(blank=True)

    # Strategy Parameters
    parameters = models.JSONField(default=dict, help_text="Strategy-specific parameters")

    # Risk Management
    max_position_size = models.DecimalField(max_digits=10, decimal_places=2, default=1000)
    max_daily_loss = models.DecimalField(max_digits=10, decimal_places=2, default=500)
    max_drawdown = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)

    # Activation
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Performance Tracking
    total_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    win_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trading_strategy'
        verbose_name = 'Trading Strategy'
        verbose_name_plural = 'Trading Strategies'
        indexes = [
            models.Index(fields=['strategy_type', 'is_active']),
        ]

class ExecutionLog(models.Model):
    """
    Audit log for all trading executions
    """
    LOG_LEVELS = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('EXECUTION', 'Execution'),
    ]

    trading_account = models.ForeignKey(TradingAccount, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)

    level = models.CharField(max_length=20, choices=LOG_LEVELS)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'execution_log'
        verbose_name = 'Execution Log'
        verbose_name_plural = 'Execution Logs'
        indexes = [
            models.Index(fields=['trading_account', 'created_at']),
            models.Index(fields=['level', 'created_at']),
        ]
        ordering = ['-created_at']

class RiskCheck(models.Model):
    """
    Pre-trade risk checks and validations
    """
    trading_account = models.ForeignKey(TradingAccount, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    CHECK_TYPES = [
        ('POSITION_SIZE', 'Position Size'),
        ('DAY_TRADING', 'Day Trading'),
        ('MARGIN', 'Margin'),
        ('VOLATILITY', 'Volatility'),
        ('LIQUIDITY', 'Liquidity'),
    ]

    check_type = models.CharField(max_length=20, choices=CHECK_TYPES)
    passed = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)

    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'risk_check'
        verbose_name = 'Risk Check'
        verbose_name_plural = 'Risk Checks'
        indexes = [
            models.Index(fields=['trading_account', 'checked_at']),
            models.Index(fields=['passed', 'check_type']),
        ]