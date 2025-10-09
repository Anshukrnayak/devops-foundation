# apps/trading/brokers/alpaca_broker.py
import alpaca_trade_api as tradeapi
from decimal import Decimal
from typing import Dict, List, Optional, Any
import logging
from django.utils import timezone
from .base_broker import BaseBroker

logger = logging.getLogger(__name__)

class AlpacaBroker(BaseBroker):
    """
    Alpaca Markets broker implementation
    Supports both paper and live trading
    """

    def __init__(self, api_key: str, secret_key: str, base_url: str = None, paper_trading: bool = True):
        if not base_url:
            base_url = 'https://paper-api.alpaca.markets' if paper_trading else 'https://api.alpaca.markets'

        super().__init__('Alpaca', api_key, secret_key, base_url, paper_trading)
        self.api = None
        self.rate_limits = {
            'requests_per_minute': 200,
            'orders_per_second': 10
        }

    def connect(self) -> bool:
        """
        Connect to Alpaca API
        """
        try:
            self.api = tradeapi.REST(
                self.api_key,
                self.secret_key,
                self.base_url,
                api_version='v2'
            )

            # Test connection with account info
            account = self.api.get_account()
            self.is_connected = True
            self.last_connection_test = timezone.now()

            logger.info(f"Successfully connected to Alpaca ({'Paper' if self.paper_trading else 'Live'})")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Alpaca: {str(e)}")
            self.is_connected = False
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from Alpaca API
        """
        try:
            # Alpaca REST API doesn't require explicit disconnection
            self.api = None
            self.is_connected = False
            logger.info("Disconnected from Alpaca")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from Alpaca: {str(e)}")
            return False

    def get_account_info(self) -> Dict[str, Any]:
        """
        Get Alpaca account information
        """
        if not self.is_connected:
            self.connect()

        try:
            account = self.api.get_account()

            return {
                'account_number': account.account_number,
                'status': account.status,
                'currency': account.currency,
                'buying_power': Decimal(account.buying_power),
                'cash': Decimal(account.cash),
                'portfolio_value': Decimal(account.portfolio_value),
                'initial_margin': Decimal(account.initial_margin),
                'maintenance_margin': Decimal(account.maintenance_margin),
                'day_trade_count': int(account.daytrade_count),
                'last_equity': Decimal(account.last_equity),
                'long_market_value': Decimal(account.long_market_value),
                'short_market_value': Decimal(account.short_market_value),
                'equity': Decimal(account.equity),
                'last_maintenance_margin': Decimal(account.last_maintenance_margin),
            }

        except Exception as e:
            logger.error(f"Error getting Alpaca account info: {str(e)}")
            raise

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions from Alpaca
        """
        if not self.is_connected:
            self.connect()

        try:
            positions = self.api.list_positions()
            formatted_positions = []

            for position in positions:
                formatted_positions.append({
                    'symbol': position.symbol,
                    'quantity': Decimal(position.qty),
                    'current_price': Decimal(position.current_price),
                    'market_value': Decimal(position.market_value),
                    'average_entry_price': Decimal(position.avg_entry_price),
                    'unrealized_pl': Decimal(position.unrealized_pl),
                    'unrealized_plpc': Decimal(position.unrealized_plpc),
                    'side': 'LONG' if Decimal(position.qty) > 0 else 'SHORT',
                    'asset_class': position.asset_class,
                })

            return formatted_positions

        except Exception as e:
            logger.error(f"Error getting Alpaca positions: {str(e)}")
            raise

    def get_orders(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Get order history from Alpaca
        """
        if not self.is_connected:
            self.connect()

        try:
            # Map status to Alpaca status
            status_map = {
                'PENDING': 'pending',
                'SUBMITTED': 'submitted',
                'FILLED': 'filled',
                'CANCELLED': 'canceled',
                'REJECTED': 'rejected'
            }

            alpaca_status = status_map.get(status) if status else None
            orders = self.api.list_orders(status=alpaca_status, limit=100)

            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    'order_id': order.id,
                    'client_order_id': order.client_order_id,
                    'symbol': order.symbol,
                    'quantity': Decimal(order.qty),
                    'filled_quantity': Decimal(order.filled_qty) if order.filled_qty else Decimal('0'),
                    'side': order.side.upper(),
                    'order_type': order.type.upper(),
                    'time_in_force': order.time_in_force.upper(),
                    'status': order.status.upper(),
                    'limit_price': Decimal(order.limit_price) if order.limit_price else None,
                    'stop_price': Decimal(order.stop_price) if order.stop_price else None,
                    'filled_avg_price': Decimal(order.filled_avg_price) if order.filled_avg_price else None,
                    'created_at': order.created_at,
                    'updated_at': order.updated_at,
                    'submitted_at': order.submitted_at,
                    'filled_at': order.filled_at,
                })

            return formatted_orders

        except Exception as e:
            logger.error(f"Error getting Alpaca orders: {str(e)}")
            raise

    def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place order with Alpaca
        """
        if not self.is_connected:
            self.connect()

        try:
            # Validate required fields
            required_fields = ['symbol', 'side', 'order_type', 'quantity', 'time_in_force']
            for field in required_fields:
                if field not in order_data:
                    raise ValueError(f"Missing required field: {field}")

            # Prepare order parameters
            order_params = {
                'symbol': order_data['symbol'],
                'qty': float(order_data['quantity']),
                'side': order_data['side'].lower(),
                'type': order_data['order_type'].lower(),
                'time_in_force': order_data['time_in_force'].lower(),
            }

            # Add optional parameters
            if 'limit_price' in order_data and order_data['limit_price']:
                order_params['limit_price'] = float(order_data['limit_price'])

            if 'stop_price' in order_data and order_data['stop_price']:
                order_params['stop_price'] = float(order_data['stop_price'])

            if 'client_order_id' in order_data:
                order_params['client_order_id'] = order_data['client_order_id']

            # Submit order
            order = self.api.submit_order(**order_params)

            # Format response
            response = {
                'success': True,
                'order_id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'status': order.status.upper(),
                'submitted_at': order.submitted_at,
                'broker_response': order._raw
            }

            logger.info(f"Order placed successfully: {order.id} for {order.symbol}")
            return response

        except tradeapi.rest.APIError as e:
            error_msg = f"Alpaca API error: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'order_id': None
            }
        except Exception as e:
            error_msg = f"Error placing order with Alpaca: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'order_id': None
            }

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel order with Alpaca
        """
        if not self.is_connected:
            self.connect()

        try:
            self.api.cancel_order(order_id)
            logger.info(f"Order cancelled successfully: {order_id}")
            return True

        except tradeapi.rest.APIError as e:
            if 'order not found' in str(e).lower():
                logger.warning(f"Order not found, may already be filled or cancelled: {order_id}")
                return True
            else:
                logger.error(f"Error cancelling order {order_id}: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get order status from Alpaca
        """
        if not self.is_connected:
            self.connect()

        try:
            order = self.api.get_order(order_id)

            return {
                'order_id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'quantity': Decimal(order.qty),
                'filled_quantity': Decimal(order.filled_qty) if order.filled_qty else Decimal('0'),
                'side': order.side.upper(),
                'order_type': order.type.upper(),
                'status': order.status.upper(),
                'limit_price': Decimal(order.limit_price) if order.limit_price else None,
                'stop_price': Decimal(order.stop_price) if order.stop_price else None,
                'filled_avg_price': Decimal(order.filled_avg_price) if order.filled_avg_price else None,
                'created_at': order.created_at,
                'updated_at': order.updated_at,
                'submitted_at': order.submitted_at,
                'filled_at': order.filled_at,
            }

        except Exception as e:
            logger.error(f"Error getting order status {order_id}: {str(e)}")
            raise

    def get_market_data(self, symbol: str, timeframe: str = '1D', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get market data from Alpaca
        """
        if not self.is_connected:
            self.connect()

        try:
            # Map timeframe to Alpaca timeframe
            timeframe_map = {
                '1Min': '1Min',
                '5Min': '5Min',
                '15Min': '15Min',
                '1H': '1H',
                '1D': '1D'
            }

            alpaca_timeframe = timeframe_map.get(timeframe, '1D')
            bars = self.api.get_barset(symbol, alpaca_timeframe, limit=limit)[symbol]

            market_data = []
            for bar in bars:
                market_data.append({
                    'timestamp': bar.t,
                    'open': Decimal(str(bar.o)),
                    'high': Decimal(str(bar.h)),
                    'low': Decimal(str(bar.l)),
                    'close': Decimal(str(bar.c)),
                    'volume': int(bar.v),
                })

            return market_data

        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {str(e)}")
            raise

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote from Alpaca
        """
        if not self.is_connected:
            self.connect()

        try:
            quote = self.api.get_last_quote(symbol)

            return {
                'symbol': symbol,
                'bid_price': Decimal(str(quote.bidprice)),
                'bid_size': int(quote.bidsize),
                'ask_price': Decimal(str(quote.askprice)),
                'ask_size': int(quote.asksize),
                'timestamp': quote.timestamp,
            }

        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            raise

    def get_supported_order_types(self) -> List[str]:
        """
        Get supported order types for Alpaca
        """
        return ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT', 'TRAILING_STOP']

    def get_supported_assets(self) -> List[str]:
        """
        Get supported asset types for Alpaca
        """
        return ['STOCK', 'ETF', 'CRYPTO']