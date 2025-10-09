# apps/trading/executors/__init__.py
from typing import Type, Dict
from .base_executor import BaseOrderExecutor
from .immediate_executor import ImmediateOrderExecutor
from .smart_router import SmartOrderRouter

class ExecutorFactory:
    """
    Factory class for creating order executors
    """

    @staticmethod
    def create_executor(executor_type: str, broker, trading_account) -> BaseOrderExecutor:
        """
        Create executor instance based on type
        """
        executors: Dict[str, Type[BaseOrderExecutor]] = {
            'IMMEDIATE': ImmediateOrderExecutor,
            'SMART_ROUTER': SmartOrderRouter,
        }

        if executor_type not in executors:
            raise ValueError(f"Unsupported executor type: {executor_type}")

        executor_class = executors[executor_type]
        return executor_class(broker, trading_account)

    @staticmethod
    def get_available_executors() -> Dict[str, str]:
        """
        Return available executor types and their descriptions
        """
        return {
            'IMMEDIATE': 'Immediate Execution - Fast, simple order placement',
            'SMART_ROUTER': 'Smart Order Router - Advanced execution algorithms',
        }

    @staticmethod
    def get_recommended_executor(order_size: float, symbol: str, order_type: str) -> str:
        """
        Get recommended executor based on order characteristics
        """
        # Large orders benefit from smart routing
        if order_size > 10000:
            return 'SMART_ROUTER'

        # Market orders can use immediate execution
        if order_type == 'MARKET':
            return 'IMMEDIATE'

        # Default to immediate for most cases
        return 'IMMEDIATE'