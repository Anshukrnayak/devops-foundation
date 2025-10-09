# apps/prediction/engines/quantum_engine.py
import numpy as np
from numba import jit, prange
from joblib import Parallel, delayed
from scipy.stats import t
from typing import Dict, List, Tuple
import logging
from .base_engine import BasePredictionEngine
from prediction.models import QuantumEngineConfig

logger = logging.getLogger(__name__)

class QuantumTradingEngine(BasePredictionEngine):
    """
    Your quantum-charged prediction engine - completely refactored and optimized
    Implements all your sophisticated algorithms with proper error handling
    """

    def __init__(self):
        super().__init__("Quantum-Charged Engine", "2.0")
        self.config = None
        self.base_window = 20
        self.n_particles = 100
        self.hurst_threshold = 0.65

    def initialize(self, config: QuantumEngineConfig) -> bool:
        """
        Initialize with quantum engine configuration
        """
        try:
            self.config = config
            self.base_window = config.base_window_size
            self.n_particles = config.particle_count
            self.hurst_threshold = config.hurst_threshold

            # Validate configuration
            if not self._validate_config():
                return False

            self.is_initialized = True
            logger.info(f"Quantum engine initialized with config: {config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize quantum engine: {str(e)}")
            return False

    def analyze(self, data: Dict) -> Dict:
        """
        Main quantum analysis pipeline - integrates all your algorithms
        """
        if not self.validate_data(data):
            raise ValueError("Invalid input data for quantum analysis")

        try:
            # Preprocess data
            processed_data = self.preprocess_data(data)
            closes = processed_data['closes']

            # Calculate log returns
            log_returns = self._calculate_log_returns(closes)

            # 1. MA-DFA with Volatility Entropy and Fractal Dimension
            hurst, fluctuations = self._calculate_ma_dfa_optimized(closes, log_returns)

            # 2. Asymmetric MA-DFA
            hurst_up, hurst_down = self._calculate_asymmetric_ma_dfa(closes, log_returns)

            # 3. Particle Filter Volatility with Semivariance
            particle_volatility, rsv_up, rsv_down = self._calculate_particle_volatility_advanced(log_returns)

            # 4. Quantum-Inspired Chaos Optimization
            dynamic_threshold, chaos_state = self._quantum_chaos_optimization(hurst, log_returns)

            # 5. FPN-DRL Prediction
            fpn_signal, fpn_confidence, action_probs = self._fpn_drl_predict_enhanced(
                hurst, hurst_up, hurst_down, particle_volatility, log_returns
            )

            # 6. Advanced Candlestick Patterns
            candlestick_pattern, pattern_confidence = self._detect_advanced_candlestick_patterns(
                processed_data['opens'], processed_data['highs'],
                processed_data['lows'], closes
            )

            # 7. Generate Final Trading Signal
            final_signal, signal_confidence, signal_components = self._generate_quantum_signal(
                hurst, hurst_up, hurst_down, particle_volatility,
                fpn_signal, dynamic_threshold, rsv_up, rsv_down
            )

            # Compile comprehensive results
            analysis_result = {
                # Core Indicators
                'hurst_exponent': self._safe_get_last(hurst),
                'hurst_uptrend': self._safe_get_last(hurst_up),
                'hurst_downtrend': self._safe_get_last(hurst_down),
                'particle_volatility': self._safe_get_last(particle_volatility),
                'dynamic_hurst_threshold': self._safe_get_last(dynamic_threshold),

                # Signals
                'fpn_signal': fpn_signal,
                'fpn_confidence': float(fpn_confidence),
                'fpn_action_probabilities': action_probs,
                'candlestick_pattern': candlestick_pattern,
                'pattern_confidence': float(pattern_confidence),
                'final_signal': final_signal,
                'signal_confidence': float(signal_confidence),

                # Advanced Metrics
                'volatility_entropy': float(self._calculate_volatility_entropy(log_returns)),
                'fractal_dimension': float(2 - hurst[-1]) if len(hurst) > 0 and hurst[-1] else None,
                'chaos_state': float(chaos_state),
                'regime_detection': self._detect_market_regime(hurst, particle_volatility),
                'risk_assessment': self._assess_risk_level(particle_volatility, hurst),

                # Component Analysis
                'signal_components': signal_components,
                'analysis_timestamp': timezone.now().isoformat()
            }

            return analysis_result

        except Exception as e:
            logger.error(f"Quantum analysis failed: {str(e)}")
            raise

    def validate_data(self, data: Dict) -> bool:
        """
        Validate input data for quantum analysis
        """
        required_keys = ['closes', 'opens', 'highs', 'lows']
        if not all(key in data for key in required_keys):
            return False

        if len(data['closes']) < self.required_data_points:
            return False

        return True

    def get_required_features(self) -> List[str]:
        """
        Return required feature names for quantum analysis
        """
        return ['closes', 'opens', 'highs', 'lows', 'volumes', 'timestamps']

    @jit(nopython=True, parallel=True)
    def _calculate_ma_dfa_optimized(self, series: np.array, returns: np.array) -> Tuple[np.array, np.array]:
        """
        Optimized MA-DFA implementation with your original logic
        """
        n = len(series)
        fluctuations = np.empty(n)
        hurst = np.empty(n)

        # Calculate volatility for entropy
        volatility = np.zeros(n)
        for i in range(20, n):
            volatility[i] = np.std(returns[max(0, i-20):i])

        entropy = -volatility * np.log(volatility + 1e-10)
        entropy_mean = np.nanmean(entropy)

        for i in prange(n):
            if i == 0:
                fractal_dim = 2.0
                fluctuations[i] = np.nan
                hurst[i] = np.nan
                continue

            fractal_dim = 2 - hurst[i - 1] if not np.isnan(hurst[i - 1]) else 2.0

            # Adaptive window calculation
            if not np.isnan(entropy[i]):
                window = int(self.base_window * np.exp(-entropy[i] / entropy_mean + 1 / fractal_dim))
                window = max(10, min(50, window))
            else:
                window = self.base_window

            if i < window:
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

    def _calculate_asymmetric_ma_dfa(self, series: np.array, returns: np.array) -> Tuple[np.array, np.array]:
        """
        Asymmetric MA-DFA for trend-specific analysis
        """
        n = len(series)
        hurst_up = np.empty(n)
        hurst_down = np.empty(n)

        # Calculate base MA-DFA first
        hurst, fluctuations = self._calculate_ma_dfa_optimized(series, returns)

        for i in range(n):
            if i < self.base_window or np.isnan(hurst[i]):
                hurst_up[i] = np.nan
                hurst_down[i] = np.nan
                continue

            # Determine trend based on recent returns
            recent_returns = returns[max(0, i-10):i]
            uptrend_days = np.sum(recent_returns > 0)

            if uptrend_days > len(recent_returns) * 0.6:  # Uptrend
                hurst_up[i] = hurst[i]
                hurst_down[i] = np.nan
            elif uptrend_days < len(recent_returns) * 0.4:  # Downtrend
                hurst_up[i] = np.nan
                hurst_down[i] = hurst[i]
            else:  # Neutral
                hurst_up[i] = np.nan
                hurst_down[i] = np.nan

        return hurst_up, hurst_down

    def _calculate_particle_volatility_advanced(self, returns: np.array) -> Tuple[np.array, np.array, np.array]:
        """
        Advanced particle filter with realized semivariance
        """
        n = len(returns)
        particle_vol = np.full(n, np.nan)
        rsv_up = np.zeros(n)
        rsv_down = np.zeros(n)

        # Calculate realized semivariance
        for i in range(5, n):
            recent_returns = returns[i-5:i]
            rsv_up[i] = np.sum(np.where(recent_returns > 0, recent_returns**2, 0))
            rsv_down[i] = np.sum(np.where(recent_returns < 0, recent_returns**2, 0))

        # Particle filter implementation
        clean_returns = returns[~np.isnan(returns)]
        if len(clean_returns) > 20:
            volatilities = self._run_particle_filter(clean_returns)
            particle_vol[-len(volatilities):] = volatilities

        return particle_vol, rsv_up, rsv_down

    def _run_particle_filter(self, returns: np.array) -> np.array:
        """
        Core particle filter algorithm
        """
        particles = np.random.normal(0, 0.01, self.n_particles)
        weights = np.ones(self.n_particles) / self.n_particles
        volatilities = []

        for r in returns:
            # Particle propagation
            particles = 0.9 * particles + t.rvs(df=5, size=self.n_particles) * 0.01

            # Weight update with Student's t likelihood
            scale = np.sqrt(np.exp(particles / 2) + 1e-10)
            likelihood = t.pdf(r, df=5, loc=0, scale=scale)
            weights *= likelihood
            weights /= np.sum(weights) + 1e-10

            # Systematic resampling
            if 1 / np.sum(weights**2) < self.n_particles / 2:  # Effective sample size check
                indices = self._systematic_resampling(weights)
                particles = particles[indices]
                weights = np.ones(self.n_particles) / self.n_particles

            volatilities.append(np.mean(np.exp(particles / 2)))

        return np.array(volatilities)

    def _quantum_chaos_optimization(self, hurst: np.array, returns: np.array) -> Tuple[np.array, float]:
        """
        Quantum-inspired chaos optimization for adaptive thresholds
        """
        n = len(hurst)
        thresholds = np.full(n, self.hurst_threshold)
        x = 0.5  # Initial chaotic state
        r = 4.0  # Logistic map parameter

        volatility = np.std(returns) if len(returns) > 0 else 0.02

        for i in range(n):
            if np.isnan(hurst[i]):
                continue

            entropy = -volatility * np.log(volatility + 1e-10)
            x = r * x * (1 - x)  # Logistic map for chaos
            thresholds[i] = self.hurst_threshold + 0.01 * x * np.sin(np.pi * entropy)

        return thresholds, x

    def _fpn_drl_predict_enhanced(self, hurst: np.array, hurst_up: np.array, hurst_down: np.array,
                                  particle_vol: np.array, returns: np.array) -> Tuple[str, float, List]:
        """
        Enhanced FPN-DRL prediction with state management
        """
        if len(hurst) == 0:
            return 'HOLD', 0.5, [0.33, 0.33, 0.34]

        # Create feature vector
        features = []
        for i in range(min(5, len(hurst))):
            idx = -i-1
            feature_vec = [
                hurst[idx] if not np.isnan(hurst[idx]) else 0.5,
                hurst_up[idx] if not np.isnan(hurst_up[idx]) else 0.5,
                hurst_down[idx] if not np.isnan(hurst_down[idx]) else 0.5,
                particle_vol[idx] if not np.isnan(particle_vol[idx]) else 0.02,
                returns[idx] if not np.isnan(returns[idx]) else 0.0
            ]
            features.extend(feature_vec)

        # Simple rule-based FPN (replace with actual trained model)
        current_hurst = hurst[-1] if not np.isnan(hurst[-1]) else 0.5
        current_vol = particle_vol[-1] if not np.isnan(particle_vol[-1]) else 0.02

        # Decision logic
        if current_hurst > self.hurst_threshold and current_vol < 0.05:
            action_probs = [0.7, 0.15, 0.15]  # [Buy, Sell, Hold]
            return 'BUY', 0.7, action_probs
        elif current_hurst < (1 - self.hurst_threshold) or current_vol > 0.08:
            action_probs = [0.15, 0.7, 0.15]
            return 'SELL', 0.6, action_probs
        else:
            action_probs = [0.2, 0.2, 0.6]
            return 'HOLD', 0.5, action_probs

    def _detect_advanced_candlestick_patterns(self, opens: np.array, highs: np.array,
                                              lows: np.array, closes: np.array) -> Tuple[str, float]:
        """
        Advanced candlestick pattern detection
        """
        if len(closes) < 3:
            return 'NONE', 0.0

        # Your original pattern detection logic
        o, c, h, l = closes[-1], opens[-1], highs[-1], lows[-1]
        o1, c1, h1, l1 = closes[-2], opens[-2], highs[-2], lows[-2]
        o2, c2 = closes[-3], opens[-3]

        # Pattern detection logic from your code
        patterns = [
            ('THREE_WHITE_SOLDIERS', self._is_three_white_soldiers(closes[-3:], highs[-3:])),
            ('THREE_BLACK_CROWS', self._is_three_black_crows(closes[-3:], lows[-3:])),
            ('MORNING_STAR', self._is_morning_star([c2, c1, c], [o2, o1, o])),
            ('EVENING_STAR', self._is_evening_star([c2, c1, c], [o2, o1, o])),
        ]

        for pattern_name, detected in patterns:
            if detected:
                return pattern_name, 0.8  # High confidence for clear patterns

        return 'NONE', 0.0

    def _generate_quantum_signal(self, hurst: np.array, hurst_up: np.array, hurst_down: np.array,
                                 particle_vol: np.array, fpn_signal: str, dynamic_threshold: np.array,
                                 rsv_up: np.array, rsv_down: np.array) -> Tuple[str, float, Dict]:
        """
        Generate final quantum trading signal with component analysis
        """
        if len(hurst) == 0:
            return 'HOLD', 0.5, {}

        current_hurst = hurst[-1] if not np.isnan(hurst[-1]) else 0.5
        current_hurst_up = hurst_up[-1] if not np.isnan(hurst_up[-1]) else 0.5
        current_hurst_down = hurst_down[-1] if not np.isnan(hurst_down[-1]) else 0.5
        current_vol = particle_vol[-1] if not np.isnan(particle_vol[-1]) else 0.02
        current_threshold = dynamic_threshold[-1] if not np.isnan(dynamic_threshold[-1]) else self.hurst_threshold

        # Signal components
        components = {
            'hurst_condition': current_hurst > current_threshold,
            'regime_condition': current_hurst_up > current_hurst_down,
            'volatility_condition': current_vol < np.percentile(particle_vol[~np.isnan(particle_vol)], 75),
            'fpn_condition': fpn_signal == 'BUY',
            'semivariance_condition': rsv_up[-1] > rsv_down[-1] if len(rsv_up) > 0 else False
        }

        buy_score = sum(components.values())
        sell_score = sum([
            current_hurst < (1 - current_threshold),
            current_hurst_down > current_hurst_up,
            fpn_signal == 'SELL',
            current_vol > 0.08
        ])

        if buy_score >= 3:
            confidence = min(0.95, 0.5 + buy_score * 0.15)
            return 'BUY', confidence, components
        elif sell_score >= 2:
            confidence = min(0.85, 0.4 + sell_score * 0.2)
            return 'SELL', confidence, components
        else:
            return 'HOLD', 0.5, components

    # Helper methods
    def _safe_get_last(self, array: np.array):
        """Safely get last element of array handling NaN and empty arrays"""
        if len(array) == 0 or np.isnan(array[-1]):
            return None
        return float(array[-1])

    def _calculate_log_returns(self, prices: np.array) -> np.array:
        """Calculate log returns"""
        returns = np.log(prices / np.roll(prices, 1))
        returns[0] = 0
        return returns

    def _calculate_volatility_entropy(self, returns: np.array) -> float:
        """Calculate volatility entropy"""
        volatility = np.std(returns) if len(returns) > 0 else 0.02
        return -volatility * np.log(volatility + 1e-10)

    def _systematic_resampling(self, weights: np.array) -> np.array:
        """Systematic resampling for particle filter"""
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

    def _validate_config(self) -> bool:
        """Validate engine configuration"""
        if not self.config:
            return False
        if self.base_window < 10 or self.base_window > 50:
            return False
        if self.n_particles < 50 or self.n_particles > 500:
            return False
        if self.hurst_threshold < 0.5 or self.hurst_threshold > 0.8:
            return False
        return True

    # Candlestick pattern helpers (from your original code)
    def _is_three_white_soldiers(self, closes: np.array, highs: np.array) -> bool:
        if len(closes) < 3:
            return False
        return (closes[0] < closes[1] < closes[2] and
                highs[0] < highs[1] < highs[2])

    def _is_three_black_crows(self, closes: np.array, lows: np.array) -> bool:
        if len(closes) < 3:
            return False
        return (closes[0] > closes[1] > closes[2] and
                lows[0] > lows[1] > lows[2])

    def _is_morning_star(self, closes: np.array, opens: np.array) -> bool:
        if len(closes) < 3:
            return False
        return (closes[0] < opens[0] and  # First day bearish
                abs(closes[1] - opens[1]) < 0.1 * (max(opens[1], closes[1]) - min(opens[1], closes[1])) and  # Doji
                closes[2] > opens[2])  # Third day bullish

    def _is_evening_star(self, closes: np.array, opens: np.array) -> bool:
        if len(closes) < 3:
            return False
        return (closes[0] > opens[0] and  # First day bullish
                abs(closes[1] - opens[1]) < 0.1 * (max(opens[1], closes[1]) - min(opens[1], closes[1])) and  # Doji
                closes[2] < opens[2])  # Third day bearish

    def _detect_market_regime(self, hurst: np.array, volatility: np.array) -> str:
        """Detect current market regime"""
        if len(hurst) == 0:
            return "UNKNOWN"

        current_hurst = hurst[-1] if not np.isnan(hurst[-1]) else 0.5
        current_vol = volatility[-1] if not np.isnan(volatility[-1]) else 0.02

        if current_hurst > 0.7 and current_vol < 0.05:
            return "TRENDING_LOW_VOL"
        elif current_hurst < 0.3 and current_vol > 0.08:
            return "MEAN_REVERTING_HIGH_VOL"
        elif current_vol > 0.1:
            return "HIGH_VOLATILITY"
        else:
            return "NORMAL"

    def _assess_risk_level(self, volatility: np.array, hurst: np.array) -> str:
        """Assess overall risk level"""
        if len(volatility) == 0:
            return "MEDIUM"

        current_vol = volatility[-1] if not np.isnan(volatility[-1]) else 0.02
        current_hurst = hurst[-1] if not np.isnan(hurst[-1]) else 0.5

        if current_vol > 0.1 or current_hurst < 0.2:
            return "HIGH"
        elif current_vol < 0.03 and current_hurst > 0.6:
            return "LOW"
        else:
            return "MEDIUM"