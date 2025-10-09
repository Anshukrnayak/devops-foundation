# apps/prediction/engines/technical_engine.py
import numpy as np
import pandas as pd
import talib
from typing import Dict, List
from .base_engine import BasePredictionEngine

class TechnicalAnalysisEngine(BasePredictionEngine):
    """
    Traditional technical analysis engine
    Provides classic indicators for comparison
    """

    def __init__(self):
        super().__init__("Technical Analysis Engine", "1.0")

    def initialize(self, config: Dict) -> bool:
        self.is_initialized = True
        return True

    def analyze(self, data: Dict) -> Dict:
        closes = data['closes']

        # Calculate various technical indicators
        sma_20 = talib.SMA(closes, timeperiod=20)
        sma_50 = talib.SMA(closes, timeperiod=50)

        rsi = talib.RSI(closes, timeperiod=14)
        macd, macd_signal, macd_hist = talib.MACD(closes)

        bollinger_upper, bollinger_middle, bollinger_lower = talib.BBANDS(closes)

        stoch_k, stoch_d = talib.STOCH(closes, closes, closes)

        # Generate signals
        signals = self._generate_technical_signals(
            closes, sma_20, sma_50, rsi, macd, bollinger_upper, bollinger_lower
        )

        return {
            'sma_20': self._safe_get_last(sma_20),
            'sma_50': self._safe_get_last(sma_50),
            'rsi': self._safe_get_last(rsi),
            'macd': self._safe_get_last(macd),
            'macd_signal': self._safe_get_last(macd_signal),
            'bollinger_upper': self._safe_get_last(bollinger_upper),
            'bollinger_lower': self._safe_get_last(bollinger_lower),
            'technical_signals': signals
        }

    def _generate_technical_signals(self, closes, sma_20, sma_50, rsi, macd, bb_upper, bb_lower):
        """Generate trading signals from technical indicators"""
        signals = {}

        # Moving average crossover
        signals['ma_crossover'] = sma_20[-1] > sma_50[-1] if None not in [sma_20[-1], sma_50[-1]] else False

        # RSI signals
        signals['rsi_oversold'] = rsi[-1] < 30 if rsi[-1] else False
        signals['rsi_overbought'] = rsi[-1] > 70 if rsi[-1] else False

        # MACD signals
        signals['macd_bullish'] = macd[-1] > 0 if macd[-1] else False

        # Bollinger Bands
        signals['bb_oversold'] = closes[-1] < bb_lower[-1] if bb_lower[-1] else False
        signals['bb_overbought'] = closes[-1] > bb_upper[-1] if bb_upper[-1] else False

        return signals

    def validate_data(self, data: Dict) -> bool:
        return 'closes' in data and len(data['closes']) >= 50

    def get_required_features(self) -> List[str]:
        return ['closes']