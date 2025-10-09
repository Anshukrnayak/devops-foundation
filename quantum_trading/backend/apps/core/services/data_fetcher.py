# apps/core/services/data_fetcher.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
import logging
from typing import Dict, List, Optional
from core.models.market_data import Asset, MarketData

logger = logging.getLogger(__name__)

class MarketDataFetcher:
    """
    Robust market data fetching service with caching and error handling
    """

    def __init__(self):
        self.cache_timeout = 300  # 5 minutes

    def fetch_asset_data(self, symbol: str, days_back: int = 60) -> pd.DataFrame:
        """
        Fetch market data for a symbol with caching
        """
        cache_key = f"market_data_{symbol}_{days_back}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            logger.info(f"Using cached data for {symbol}")
            return pd.DataFrame(cached_data)

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            data = yf.download(symbol, start=start_date, end=end_date, progress=False)

            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()

            # Cache the successful result
            cache.set(cache_key, data.to_dict('records'), self.cache_timeout)
            logger.info(f"Fetched and cached data for {symbol}")

            return data

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise

    def update_asset_in_database(self, symbol: str) -> Dict:
        """
        Update market data in database for a symbol
        """
        try:
            asset, created = Asset.objects.get_or_create(
                symbol=symbol,
                defaults={'name': symbol, 'asset_type': 'STOCK'}
            )

            data = self.fetch_asset_data(symbol)

            if data.empty:
                return {'success': False, 'message': f'No data for {symbol}'}

            saved_records = 0
            with transaction.atomic():
                for index, row in data.iterrows():
                    market_data, created = MarketData.objects.update_or_create(
                        asset=asset,
                        timestamp=index.to_pydatetime(),
                        defaults={
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(row['Volume']),
                        }
                    )
                    if created:
                        saved_records += 1

            # Clear cache to force refresh next time
            cache.delete(f"market_data_{symbol}_*")

            return {
                'success': True,
                'asset': symbol,
                'saved_records': saved_records,
                'message': f'Updated {saved_records} records for {symbol}'
            }

        except Exception as e:
            logger.error(f"Error updating asset {symbol}: {str(e)}")
            return {'success': False, 'message': str(e)}

class RealTimeDataService:
    """
    Real-time data streaming and management
    """

    def __init__(self):
        self.websocket_manager = None

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get latest price from cache or database
        """
        cache_key = f"latest_price_{symbol}"
        latest_price = cache.get(cache_key)

        if latest_price is not None:
            return latest_price

        try:
            asset = Asset.objects.get(symbol=symbol)
            latest_data = MarketData.objects.filter(asset=asset).order_by('-timestamp').first()

            if latest_data:
                cache.set(cache_key, float(latest_data.close), 60)  # Cache for 1 minute
                return float(latest_data.close)

        except Asset.DoesNotExist:
            logger.error(f"Asset {symbol} not found")

        return None