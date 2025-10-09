# apps/core/models/system.py
class SystemLog(models.Model):
    """
    System monitoring and audit logs
    """
    LOG_LEVELS = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    level = models.CharField(max_length=10, choices=LOG_LEVELS)
    component = models.CharField(max_length=100)  # prediction_engine, data_fetcher, etc.
    message = models.TextField()
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    # Additional context
    traceback = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'system_log'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['level', 'component']),
        ]

class PerformanceMetric(models.Model):
    """
    System performance monitoring
    """
    component = models.CharField(max_length=100)
    metric_name = models.CharField(max_length=100)
    metric_value = models.DecimalField(max_digits=15, decimal_places=6)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'performance_metric'
        indexes = [
            models.Index(fields=['component', 'metric_name', 'recorded_at']),
        ]