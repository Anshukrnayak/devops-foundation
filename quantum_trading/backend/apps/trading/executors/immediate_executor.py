# apps/trading/executors/immediate_executor.py
from typing import Dict, List, Any
from decimal import Decimal
import logging
from django.utils import timezone
from .base_executor import BaseOrderExecutor
from trading.models import Order, Trade

logger = logging.getLogger(__name__)

class ImmediateOrderExecutor(BaseOrderExecutor):
    """
    Immediate order execution - places orders directly with broker
    Simple and fast execution strategy
    """

    def __init__(self, broker, trading_account):
        super().__init__(broker, trading_account)
        self.execution_history = []

    def execute_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute order immediately with broker
        """
        try:
            # Validate order
            validation = self.validate_order(order_data)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': '; '.join(validation['errors']),
                    'order_id': None
                }

            # Format order data
            formatted_data = self.format_order_data(order_data)

            # Create order record in database
            db_order = self._create_order_record(formatted_data)

            # Execute with broker
            broker_response = self.broker.place_order(formatted_data)

            # Update order record with broker response
            if broker_response['success']:
                db_order.broker_order_id = broker_response['order_id']
                db_order.status = 'SUBMITTED'
                db_order.submitted_at = timezone.now()
                db_order.save()

                # Add to pending orders for monitoring
                self.pending_orders[broker_response['order_id']] = {
                    'db_order_id': db_order.id,
                    'submitted_at': timezone.now(),
                    'symbol': formatted_data['symbol']
                }

            # Log execution
            self._log_execution(db_order, broker_response)

            return broker_response

        except Exception as e:
            logger.error(f"Error in immediate order execution: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'order_id': None
            }

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel order immediately
        """
        try:
            # Cancel with broker
            success = self.broker.cancel_order(order_id)

            if success:
                # Update order record
                try:
                    order = Order.objects.get(broker_order_id=order_id)
                    order.status = 'CANCELLED'
                    order.cancelled_at = timezone.now()
                    order.save()

                    # Remove from pending orders
                    if order_id in self.pending_orders:
                        del self.pending_orders[order_id]

                except Order.DoesNotExist:
                    logger.warning(f"Order {order_id} not found in database")

            return success

        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return False

    def monitor_orders(self) -> List[Dict[str, Any]]:
        """
        Monitor pending orders and update their status
        """
        updates = []

        for broker_order_id, order_info in list(self.pending_orders.items()):
            try:
                # Get current status from broker
                status_info = self.broker.get_order_status(broker_order_id)

                # Update database record
                order = Order.objects.get(broker_order_id=broker_order_id)
                order.status = status_info['status']

                if status_info.get('filled_quantity'):
                    order.filled_quantity = status_info['filled_quantity']

                if status_info.get('filled_avg_price'):
                    order.average_fill_price = status_info['filled_avg_price']

                if status_info['status'] in ['FILLED', 'CANCELLED', 'REJECTED']:
                    # Remove from pending orders
                    del self.pending_orders[broker_order_id]

                    if status_info['status'] == 'FILLED':
                        order.filled_at = timezone.now()
                        # Create trade record
                        self._create_trade_record(order, status_info)

                order.save()
                updates.append({
                    'order_id': broker_order_id,
                    'status': status_info['status'],
                    'symbol': order_info['symbol']
                })

            except Exception as e:
                logger.error(f"Error monitoring order {broker_order_id}: {str(e)}")
                # Remove problematic order from monitoring
                del self.pending_orders[broker_order_id]

        return updates

    def _create_order_record(self, order_data: Dict[str, Any]) -> Order:
        """
        Create order record in database
        """
        order = Order.objects.create(
            trading_account=self.trading_account,
            asset_id=order_data.get('asset_id'),
            client_order_id=order_data.get('client_order_id'),
            order_type=order_data['order_type'],
            side=order_data['side'],
            quantity=Decimal(str(order_data['quantity'])),
            limit_price=Decimal(str(order_data['limit_price'])) if order_data.get('limit_price') else None,
            stop_price=Decimal(str(order_data['stop_price'])) if order_data.get('stop_price') else None,
            time_in_force=order_data.get('time_in_force', 'DAY'),
            status='PENDING'
        )
        return order

    def _create_trade_record(self, order: Order, status_info: Dict[str, Any]):
        """
        Create trade record for filled order
        """
        if order.filled_quantity and order.filled_quantity > 0:
            Trade.objects.create(
                order=order,
                asset=order.asset,
                execution_id=self._generate_client_order_id(),
                quantity=order.filled_quantity,
                price=order.average_fill_price or Decimal('0'),
                commission=Decimal('0'),  # Would be provided by broker in real implementation
                executed_at=timezone.now()
            )

    def _log_execution(self, order: Order, broker_response: Dict[str, Any]):
        """
        Log order execution for audit purposes
        """
        self.execution_history.append({
            'timestamp': timezone.now(),
            'order_id': order.id,
            'broker_order_id': broker_response.get('order_id'),
            'symbol': order.asset.symbol if order.asset else 'Unknown',
            'side': order.side,
            'quantity': float(order.quantity),
            'status': broker_response.get('status', 'UNKNOWN'),
            'success': broker_response.get('success', False)
        })

        # Keep only last 1000 executions in memory
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]