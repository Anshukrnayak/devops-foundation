# apps/prediction/services.py
import numpy as np
import pandas as pd
from numba import jit, prange
from joblib import Parallel, delayed
from scipy.stats import t
from django.utils import timezone
from typing import Dict, List, Optional, Tuple
import logging
from prediction.models import QuantumEngineConfig, QuantumPrediction
from core.models.market_data import Asset, MarketData

logger = logging.getLogger(__name__)

class QuantumTradingEngine:
    """
    Your quantum-charged prediction engine - refined and structured
    """

    def __init__(self, config: QuantumEngineConfig):
        self.config = config
        self.base_window = config.base_window_size
        self.n_particles = config.particle_count
        self.hurst_threshold = config.hurst_threshold

    def analyze(self, closes: np.array, opens: np.array, highs: np.array,
                lows: np.array, volumes: np.array, timestamps: List) -> Dict:
        """
        Main analysis pipeline - integrates all your quantum algorithms
        """
        try:
            # Calculate log returns
            log_returns = np.log(closes / np.roll(closes, 1))
            log_returns[0] = 0  # First value is NaN

            # Calculate volatility
            volatility = self._calculate_volatility(log_returns)

            # 1. MA-DFA with Volatility Entropy and Fractal Dimension
            hurst, fluctuations = self._calculate_ma_dfa(closes, volatility)

            # 2. Asymmetric MA-DFA
            hurst_up, hurst_down = self._calculate_amfdfa(closes, volatility, log_returns)

            # 3. Particle Filter Volatility with Semivariance
            particle_volatility = self._calculate_particle_volatility(log_returns)

            # 4. Quantum-Inspired Chaos Optimization
            dynamic_threshold = self._quantum_chaos_optimization(hurst, volatility)

            # 5. FPN-DRL Prediction
            fpn_signal, fpn_confidence = self._fpn_drl_predict(hurst, hurst_up, hurst_down, particle_volatility, log_returns)

            # 6. Candlestick Patterns
            candlestick_pattern = self._detect_candlestick_patterns(opens, highs, lows, closes)

            # 7. Generate Final Trading Signal
            final_signal, signal_confidence = self._generate_trading_signal(
                hurst[-1] if len(hurst) > 0 else None,
                hurst_up[-1] if len(hurst_up) > 0 else None,
                hurst_down[-1] if len(hurst_down) > 0 else None,
                particle_volatility[-1] if len(particle_volatility) > 0 else None,
                fpn_signal,
                dynamic_threshold[-1] if len(dynamic_threshold) > 0 else None
            )

            return {
                'hurst_exponent': float(hurst[-1]) if len(hurst) > 0 else None,
                'hurst_uptrend': float(hurst_up[-1]) if len(hurst_up) > 0 else None,
                'hurst_downtrend': float(hurst_down[-1]) if len(hurst_down) > 0 else None,
                'particle_volatility': float(particle_volatility[-1]) if len(particle_volatility) > 0 else None,
                'dynamic_hurst_threshold': float(dynamic_threshold[-1]) if len(dynamic_threshold) > 0 else None,
                'fpn_signal': fpn_signal,
                'fpn_confidence': float(fpn_confidence),
                'candlestick_pattern': candlestick_pattern,
                'final_signal': final_signal,
                'signal_confidence': float(signal_confidence),
                'volatility_entropy': float(self._calculate_entropy(volatility)),
                'fractal_dimension': float(2 - hurst[-1]) if hurst[-1] else None,
            }

        except Exception as e:
            logger.error(f"Error in quantum analysis: {str(e)}")
            raise

    @jit(nopython=True, parallel=True)
    def _calculate_ma_dfa(self, series: np.array, volatility: np.array) -> Tuple[np.array, np.array]:
        """
        Your MA-DFA algorithm with optimizations
        """
        n = len(series)
        fluctuations = np.empty(n)
        hurst = np.empty(n)
        entropy = -volatility * np.log(volatility + 1e-10)
        entropy_mean = np.nanmean(entropy)

        for i in prange(n):
            if i == 0:
                fractal_dim = 2.0
            else:
                fractal_dim = 2 - hurst[i - 1] if not np.isnan(hurst[i - 1]) else 2.0

            window = int(self.base_window * np.exp(-entropy[i] / entropy_mean + 1 / fractal_dim)) if not np.isnan(entropy[i]) else self.base_window
            window = max(10, min(50, window))

            if i < window - 1:
                fluctuations[i] = np.nan
                hurst[i] = np.nan
            else:
                segment = series[i - window:i]
                t_indices = np.arange(len(segment))

                # Linear detrending
                poly = np.polyfit(t_indices, segment, 1)
                detrended = segment - np.polyval(poly, t_indices)
                fluctuation = np.sqrt(np.mean(detrended ** 2))

                fluctuations[i] = fluctuation
                hurst[i] = np.log(fluctuation) / np.log(window) if fluctuation > 0 else np.nan

        return hurst, fluctuations

    def _calculate_particle_volatility(self, returns: np.array) -> np.array:
        """
        Robust particle filter volatility estimation
        """
        try:
            # Remove NaN values
            returns_clean = returns[~np.isnan(returns)]

            if len(returns_clean) == 0:
                return np.array([np.nan] * len(returns))

            # Initialize particles
            particles = np.random.normal(0, 0.01, self.n_particles)
            weights = np.ones(self.n_particles) / self.n_particles
            volatilities = []

            for r in returns_clean:
                # Particle propagation
                particles = 0.9 * particles + t.rvs(df=5, size=self.n_particles) * 0.01

                # Weight update
                scale = np.sqrt(np.exp(particles / 2))
                likelihood = t.pdf(r, df=5, loc=0, scale=scale + 1e-10)
                weights *= likelihood
                weights /= np.sum(weights) + 1e-10

                # Systematic resampling
                indices = self._systematic_resampling(weights)
                particles = particles[indices]
                weights = np.ones(self.n_particles) / self.n_particles

                # Store volatility estimate
                volatilities.append(np.mean(np.exp(particles / 2)))

            # Pad with NaN for initial values
            nan_padding = [np.nan] * (len(returns) - len(volatilities))
            return np.array(nan_padding + volatilities)

        except Exception as e:
            logger.error(f"Error in particle filter: {str(e)}")
            return np.array([np.nan] * len(returns))

    def _systematic_resampling(self, weights: np.array) -> np.array:
        """
        Systematic resampling for particle filter
        """
        n = len(weights)
        indices = np.zeros(n, dtype=int)
        cumulative_sum = np.cumsum(weights)
        step = 1.0 / n
        u = np.random.uniform(0, step)

        i = 0
        for j in range(n):
            while u > cumulative_sum[i] and i < n - 1:
                i += 1
            indices[j] = i
            u += step

        return indices

    def _fpn_drl_predict(self, hurst: np.array, hurst_up: np.array, hurst_down: np.array,
                         particle_vol: np.array, returns: np.array) -> Tuple[str, float]:
        """
        FPN-DRL prediction with proper state management
        """
        try:
            # Create state vector from recent values
            recent_data = {
                'hurst': hurst[-5:] if len(hurst) >= 5 else hurst,
                'hurst_up': hurst_up[-5:] if len(hurst_up) >= 5 else hurst_up,
                'hurst_down': hurst_down[-5:] if len(hurst_down) >= 5 else hurst_down,
                'particle_vol': particle_vol[-5:] if len(particle_vol) >= 5 else particle_vol,
                'returns': returns[-5:] if len(returns) >= 5 else returns
            }

            # Simple rule-based FPN implementation
            # In production, replace with actual trained model
            if len(hurst) == 0:
                return 'HOLD', 0.5

            current_hurst = hurst[-1] if not np.isnan(hurst[-1]) else 0.5
            current_vol = particle_vol[-1] if not np.isnan(particle_vol[-1]) else 0.02

            # Simple decision rules (replace with actual model inference)
            if current_hurst > self.hurst_threshold and current_vol < 0.05:
                return 'BUY', 0.7
            elif current_hurst < (1 - self.hurst_threshold) or current_vol > 0.08:
                return 'SELL', 0.6
            else:
                return 'HOLD', 0.5

        except Exception as e:
            logger.error(f"Error in FPN-DRL prediction: {str(e)}")
            return 'HOLD', 0.5

    def _generate_trading_signal(self, hurst: float, hurst_up: float, hurst_down: float,
                                 particle_vol: float, fpn_signal: str, dynamic_threshold: float) -> Tuple[str, float]:
        """
        Generate final trading signal based on all indicators
        """
        try:
            if any(v is None or np.isnan(v) for v in [hurst, hurst_up, hurst_down, particle_vol, dynamic_threshold]):
                return 'HOLD', 0.5

            # Your trading logic from generate_trading_signals
            vol_threshold = np.percentile([particle_vol], 75)  # Simplified

            buy_conditions = [
                hurst > dynamic_threshold,
                hurst_up > hurst_down if hurst_up and hurst_down else False,
                particle_vol < vol_threshold,
                fpn_signal == 'BUY'
            ]

            sell_conditions = [
                hurst < (1 - dynamic_threshold),
                hurst_down > hurst_up if hurst_up and hurst_down else False,
                fpn_signal == 'SELL'
            ]

            buy_score = sum(buy_conditions)
            sell_score = sum(sell_conditions)

            if buy_score >= 3:
                return 'BUY', min(0.9, 0.5 + buy_score * 0.1)
            elif sell_score >= 2:
                return 'SELL', min(0.8, 0.4 + sell_score * 0.2)
            else:
                return 'HOLD', 0.5

        except Exception as e:
            logger.error(f"Error generating trading signal: {str(e)}")
            return 'HOLD', 0.5

class PredictionOrchestrator:
    """
    Orchestrates the complete prediction pipeline
    """

    def __init__(self):
        self.quantum_engine = None

    def run_prediction_pipeline(self, asset_symbol: str) -> Dict:
        """
        Run complete prediction pipeline for an asset
        """
        try:
            # Get latest engine config
            config = QuantumEngineConfig.objects.filter(is_active=True).first()
            if not config:
                config = QuantumEngineConfig.objects.create(
                    name="Default Quantum Engine",
                    base_window_size=20,
                    particle_count=100,
                    hurst_threshold=0.65
                )

            self.quantum_engine = QuantumTradingEngine(config)

            # Fetch market data
            asset = Asset.objects.get(symbol=asset_symbol)
            market_data = MarketData.objects.filter(asset=asset).order_by('-timestamp')[:100]

            if len(market_data) < 50:
                raise ValueError(f"Insufficient data for {asset_symbol}")

            # Prepare data arrays
            data_arrays = self._prepare_data_arrays(market_data)

            # Run quantum analysis
            analysis_result = self.quantum_engine.analyze(**data_arrays)

            return {
                'success': True,
                'asset': asset_symbol,
                'analysis': analysis_result,
                'timestamp': timezone.now()
            }

        except Exception as e:
            logger.error(f"Error in prediction pipeline for {asset_symbol}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'asset': asset_symbol
            }

    def _prepare_data_arrays(self, market_data) -> Dict:
        """
        Prepare numpy arrays from market data
        """
        closes = np.array([float(data.close) for data in market_data])
        opens = np.array([float(data.open) for data in market_data])
        highs = np.array([float(data.high) for data in market_data])
        lows = np.array([float(data.low) for data in market_data])
        volumes = np.array([float(data.volume) for data in market_data])
        timestamps = [data.timestamp for data in market_data]

        return {
            'closes': closes,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'volumes': volumes,
            'timestamps': timestamps
        }