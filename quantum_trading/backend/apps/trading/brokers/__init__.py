# apps/trading/brokers/__init__.py
from typing import Type, Dict
from .base_broker import BaseBroker
from .alpaca_broker import AlpacaBroker
from .ibkr_broker import InteractiveBrokersBroker

class BrokerFactory:
    """
    Factory class for creating broker instances
    """

    @staticmethod
    def create_broker(broker_type: str, api_key: str, secret_key: str,
                      base_url: str = None, paper_trading: bool = True) -> BaseBroker:
        """
        Create broker instance based on type
        """
        brokers: Dict[str, Type[BaseBroker]] = {
            'ALPACA': AlpacaBroker,
            'INTERACTIVE_BROKERS': InteractiveBrokersBroker,
        }

        if broker_type not in brokers:
            raise ValueError(f"Unsupported broker type: {broker_type}")

        broker_class = brokers[broker_type]
        return broker_class(api_key, secret_key, base_url, paper_trading)

    @staticmethod
    def get_available_brokers() -> Dict[str, str]:
        """
        Return available broker types and their descriptions
        """
        return {
            'ALPACA': 'Alpaca Markets - Commission-free API trading',
            'INTERACTIVE_BROKERS': 'Interactive Brokers - Professional trading platform',
        }

    @staticmethod
    def get_broker_capabilities(broker_type: str) -> Dict[str, Any]:
        """
        Get capabilities for a specific broker type
        """
        broker_class = {
            'ALPACA': AlpacaBroker,
            'INTERACTIVE_BROKERS': InteractiveBrokersBroker,
        }.get(broker_type)

        if not broker_class:
            return {}

        # Create a temporary instance to get capabilities
        temp_broker = broker_class('temp', 'temp')
        return {
            'supported_order_types': temp_broker.get_supported_order_types(),
            'supported_assets': temp_broker.get_supported_assets(),
            'paper_trading': True,
            'rate_limits': temp_broker.rate_limits
        }