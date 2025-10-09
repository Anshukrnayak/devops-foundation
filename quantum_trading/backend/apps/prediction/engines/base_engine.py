# apps/prediction/engines/base_engine.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from django.utils import timezone
import logging
from core.models.market_data import Asset

logger = logging.getLogger(__name__)

class BasePredictionEngine(ABC):
    """
    Abstract base class for all prediction engines
    Defines the interface that all engines must implement
    """

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.is_initialized = False
        self.required_data_points = 50  # Minimum data required

    @abstractmethod
    def initialize(self, config: Dict) -> bool:
        """
        Initialize the engine with configuration
        """
        pass

    @abstractmethod
    def analyze(self, data: Dict) -> Dict:
        """
        Main analysis method - must be implemented by all engines
        """
        pass

    @abstractmethod
    def validate_data(self, data: Dict) -> bool:
        """
        Validate input data before processing
        """
        pass

    @abstractmethod
    def get_required_features(self) -> List[str]:
        """
        Return list of required feature names
        """
        pass

    def preprocess_data(self, data: Dict) -> Dict:
        """
        Common data preprocessing pipeline
        """
        try:
            # Convert to numpy arrays
            processed = {}
            for key, values in data.items():
                if isinstance(values, list):
                    processed[key] = np.array(values)
                else:
                    processed[key] = values

            # Handle missing values
            for key in ['closes', 'opens', 'highs', 'lows']:
                if key in processed:
                    processed[key] = self._handle_missing_values(processed[key])

            return processed

        except Exception as e:
            logger.error(f"Error in data preprocessing: {str(e)}")
            raise

    def _handle_missing_values(self, array: np.array) -> np.array:
        """
        Handle NaN values in data arrays
        """
        if np.isnan(array).any():
            # Forward fill, then backward fill
            df = pd.Series(array)
            df = df.ffill().bfill()
            return df.values
        return array

    def calculate_performance_metrics(self, predictions: List, actuals: List) -> Dict:
        """
        Calculate common performance metrics
        """
        if len(predictions) != len(actuals) or len(predictions) == 0:
            return {}

        predictions = np.array(predictions)
        actuals = np.array(actuals)

        # Calculate metrics
        mse = np.mean((predictions - actuals) ** 2)
        mae = np.mean(np.abs(predictions - actuals))
        accuracy = np.mean((predictions > 0) == (actuals > 0))  # Direction accuracy

        return {
            'mean_squared_error': float(mse),
            'mean_absolute_error': float(mae),
            'direction_accuracy': float(accuracy),
            'total_predictions': len(predictions)
        }

    def get_engine_info(self) -> Dict:
        """
        Return engine metadata
        """
        return {
            'name': self.name,
            'version': self.version,
            'initialized': self.is_initialized,
            'required_data_points': self.required_data_points,
            'timestamp': timezone.now().isoformat()
        }