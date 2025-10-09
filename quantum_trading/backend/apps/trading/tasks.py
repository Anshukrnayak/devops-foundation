# apps/trading/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from prediction.models import QuantumPrediction
from core.models.portfolios import Portfolio, Position, Trade
from core.models.signals import TradingSignal
import logging

logger = logging.getLogger(__name__)

@shared_task
def evaluate_trading_signal(prediction_id):
    """
    Evaluate a quantum prediction for potential trading action
    """
    try:
        prediction = QuantumPrediction.objects.get(id=prediction_id)

        # Check if signal meets trading criteria
        if (prediction.final_signal in ['BUY', 'SELL'] and
                prediction.signal_confidence > 0.7 and
                not prediction.signal_executed):

            logger.info(f"Evaluating trading signal for {prediction.asset.symbol}")

            # Create trading signal record
            trading_signal = TradingSignal.objects.create(
                asset=prediction.asset,
                prediction_engine=prediction.engine_config.prediction_engine,
                signal_type=prediction.final_signal,
                confidence=prediction.signal_confidence,
                target_price=prediction.market_data.close * 1.05 if prediction.final_signal == 'BUY' else prediction.market_data.close * 0.95,
                stop_loss=prediction.market_data.close * 0.95 if prediction.final_signal == 'BUY' else prediction.market_data.close * 1.05,
                timeframe='1D',
                hurst_value=prediction.hurst_exponent,
                volatility_regime='HIGH' if prediction.particle_volatility and prediction.particle_volatility > 0.02 else 'LOW',
                expires_at=timezone.now() + timedelta(hours=24)
            )

            # Mark prediction as executed
            prediction.signal_executed = True
            prediction.save()

            logger.info(f"Created trading signal {trading_signal.id} for {prediction.asset.symbol}")

            return f"Signal evaluated: {prediction.final_signal} for {prediction.asset.symbol}"
        else:
            return f"Signal does not meet trading criteria for {prediction.asset.symbol}"

    except QuantumPrediction.DoesNotExist:
        logger.error(f"Prediction {prediction_id} not found")
        return f"Prediction {prediction_id} not found"
    except Exception as e:
        logger.error(f"Error evaluating signal for prediction {prediction_id}: {str(e)}")
        return f"Signal evaluation error: {str(e)}"
