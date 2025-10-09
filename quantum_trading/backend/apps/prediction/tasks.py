# apps/prediction/tasks.py
from celery import shared_task, chain, group
from django.utils import timezone
from django.db import transaction, connection
import numpy as np
import pandas as pd
from numba import jit, prange
from joblib import Parallel, delayed
from scipy.stats import t
import warnings
warnings.filterwarnings('ignore')

from core.models.market_data import Asset, MarketData
from .models import QuantumEngineConfig, QuantumPrediction, RealTimePredictionQueue
from .engines.quantum_engine import QuantumTradingEngine
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def run_quantum_analysis(self, asset_symbol, engine_config_id=None):
    """
    Main task to run your complete quantum analysis pipeline
    """
    try:
        logger.info(f"Starting quantum analysis for {asset_symbol}")

        # Get or create engine configuration
        if engine_config_id:
            engine_config = QuantumEngineConfig.objects.get(id=engine_config_id)
        else:
            engine_config = QuantumEngineConfig.objects.filter(is_active=True).first()
            if not engine_config:
                engine_config = QuantumEngineConfig.objects.create(
                    name="Default Quantum Engine",
                    base_window_size=20,
                    particle_count=100,
                    hurst_threshold=0.65
                )

        # Get asset and recent market data
        asset = Asset.objects.get(symbol=asset_symbol)
        recent_data = MarketData.objects.filter(
            asset=asset
        ).order_by('-timestamp')[:100]  # Get last 100 records

        if len(recent_data) < 50:  # Minimum data requirement
            logger.warning(f"Insufficient data for {asset_symbol}")
            return f"Insufficient data for {asset_symbol}"

        # Convert to numpy arrays for processing
        closes = np.array([float(data.close) for data in recent_data])
        opens = np.array([float(data.open) for data in recent_data])
        highs = np.array([float(data.high) for data in recent_data])
        lows = np.array([float(data.low) for data in recent_data])
        volumes = np.array([float(data.volume) for data in recent_data])

        # Initialize quantum engine
        engine = QuantumTradingEngine(engine_config)

        # Run the complete quantum analysis pipeline
        with transaction.atomic():
            prediction_data = engine.analyze(
                closes=closes,
                opens=opens,
                highs=highs,
                lows=lows,
                volumes=volumes,
                timestamps=[data.timestamp for data in recent_data]
            )

            # Save prediction results
            latest_timestamp = recent_data[0].timestamp
            prediction, created = QuantumPrediction.objects.update_or_create(
                asset=asset,
                prediction_timestamp=latest_timestamp,
                engine_config=engine_config,
                defaults=prediction_data
            )

            logger.info(f"Quantum analysis completed for {asset_symbol}. Signal: {prediction.final_signal}")

            # Trigger trading signal evaluation if it's a strong signal
            if prediction.final_signal in ['BUY', 'SELL'] and prediction.signal_confidence > 0.7:
                from trading.tasks import evaluate_trading_signal
                evaluate_trading_signal.delay(prediction.id)

            return {
                'asset': asset_symbol,
                'signal': prediction.final_signal,
                'confidence': float(prediction.signal_confidence),
                'hurst': float(prediction.hurst_exponent) if prediction.hurst_exponent else None,
                'volatility': float(prediction.particle_volatility) if prediction.particle_volatility else None
            }

    except Asset.DoesNotExist:
        logger.error(f"Asset {asset_symbol} not found")
        return f"Asset {asset_symbol} not found"
    except Exception as exc:
        logger.error(f"Error in quantum analysis for {asset_symbol}: {str(exc)}")
        try:
            raise self.retry(countdown=120, exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for {asset_symbol}")
            return f"Quantum analysis failed for {asset_symbol}"

@shared_task
def queue_quantum_analysis(asset_symbol, priority=5):
    """
    Queue system for managing prediction requests
    """
    try:
        asset = Asset.objects.get(symbol=asset_symbol)

        # Check if there's already a pending analysis for recent data
        recent_threshold = timezone.now() - timedelta(minutes=30)
        existing_queue = RealTimePredictionQueue.objects.filter(
            asset=asset,
            status='PENDING',
            market_data_timestamp__gte=recent_threshold
        ).exists()

        if existing_queue:
            logger.info(f"Analysis already queued for {asset_symbol}")
            return f"Analysis already queued for {asset_symbol}"

        # Get latest market data timestamp
        latest_data = MarketData.objects.filter(asset=asset).order_by('-timestamp').first()
        if not latest_data:
            logger.warning(f"No market data found for {asset_symbol}")
            return f"No market data for {asset_symbol}"

        # Create queue entry
        queue_entry = RealTimePredictionQueue.objects.create(
            asset=asset,
            market_data_timestamp=latest_data.timestamp,
            priority=priority,
            status='PENDING'
        )

        # Process the queue entry
        process_prediction_queue.delay(queue_entry.id)

        logger.info(f"Queued quantum analysis for {asset_symbol}")
        return f"Queued analysis for {asset_symbol}"

    except Exception as e:
        logger.error(f"Error queueing analysis for {asset_symbol}: {str(e)}")
        return f"Queue error for {asset_symbol}"

@shared_task(bind=True)
def process_prediction_queue(self, queue_entry_id):
    """
    Process entries from the prediction queue
    """
    try:
        queue_entry = RealTimePredictionQueue.objects.get(id=queue_entry_id)

        if queue_entry.status != 'PENDING':
            logger.warning(f"Queue entry {queue_entry_id} already processed")
            return

        # Update status to processing
        queue_entry.status = 'PROCESSING'
        queue_entry.processing_started = timezone.now()
        queue_entry.save()

        # Run the quantum analysis
        result = run_quantum_analysis(
            queue_entry.asset.symbol,
            engine_config_id=None  # Use default config
        )

        # Update queue entry with results
        queue_entry.status = 'COMPLETED'
        queue_entry.completed_at = timezone.now()

        if isinstance(result, dict) and 'signal' in result:
            # Find the created prediction
            prediction = QuantumPrediction.objects.filter(
                asset=queue_entry.asset,
                prediction_timestamp=queue_entry.market_data_timestamp
            ).first()
            if prediction:
                queue_entry.prediction = prediction

        queue_entry.save()

        logger.info(f"Processed queue entry {queue_entry_id}")
        return f"Processed queue entry {queue_entry_id}"

    except RealTimePredictionQueue.DoesNotExist:
        logger.error(f"Queue entry {queue_entry_id} not found")
    except Exception as exc:
        logger.error(f"Error processing queue entry {queue_entry_id}: {str(exc)}")

        # Update queue entry with error
        try:
            queue_entry = RealTimePredictionQueue.objects.get(id=queue_entry_id)
            queue_entry.status = 'FAILED'
            queue_entry.error_message = str(exc)
            queue_entry.completed_at = timezone.now()
            queue_entry.save()
        except:
            pass

        try:
            raise self.retry(countdown=300, exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for queue entry {queue_entry_id}")

@shared_task
def batch_quantum_analysis(asset_symbols=None):
    """
    Batch process quantum analysis for multiple assets
    """
    if asset_symbols is None:
        assets = Asset.objects.filter(is_active=True)
        asset_symbols = [asset.symbol for asset in assets]

    # Create group of tasks with limited concurrency
    job = group(run_quantum_analysis.s(symbol) for symbol in asset_symbols)
    result = job.apply_async()

    logger.info(f"Started batch quantum analysis for {len(asset_symbols)} assets")
    return f"Batch analysis initiated for {len(asset_symbols)} assets"

@shared_task
def cleanup_old_predictions(days_to_keep=30):
    """
    Clean up old predictions to manage database size
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        deleted_count, _ = QuantumPrediction.objects.filter(
            prediction_timestamp__lt=cutoff_date
        ).delete()

        # Also clean up old queue entries
        queue_deleted, _ = RealTimePredictionQueue.objects.filter(
            created_at__lt=cutoff_date
        ).delete()

        logger.info(f"Cleaned up {deleted_count} old predictions and {queue_deleted} queue entries")
        return f"Cleaned up {deleted_count} predictions and {queue_deleted} queue entries"

    except Exception as e:
        logger.error(f"Error cleaning up old predictions: {str(e)}")
        return f"Cleanup error: {str(e)}"