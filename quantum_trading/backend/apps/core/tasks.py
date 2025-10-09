# apps/core/tasks.py
from celery import shared_task, group
from django.utils import timezone
from django.db import transaction
from celery.exceptions import MaxRetriesExceededError
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from .models.market_data import Asset, MarketData, TechnicalIndicator
from .services.data_fetcher import MarketDataFetcher
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def fetch_market_data(self, asset_symbol, days_back=60):
    """
    Fetch market data for a specific asset with retry logic
    """
    try:
        logger.info(f"Fetching market data for {asset_symbol}")

        asset, created = Asset.objects.get_or_create(
            symbol=asset_symbol,
            defaults={'name': asset_symbol, 'asset_type': 'STOCK'}
        )

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Fetch data using yfinance
        data = yf.download(asset_symbol, start=start_date, end=end_date, progress=False)

        if data.empty:
            logger.warning(f"No data found for {asset_symbol}")
            return f"No data for {asset_symbol}"

        # Save market data
        saved_records = 0
        for index, row in data.iterrows():
            market_data, created = MarketData.objects.update_or_create(
                asset=asset,
                timestamp=index,
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

        logger.info(f"Saved {saved_records} market records for {asset_symbol}")

        # Trigger indicator calculation
        calculate_asset_indicators.delay(asset_symbol)

        return f"Successfully processed {saved_records} records for {asset_symbol}"

    except Exception as exc:
        logger.error(f"Error fetching data for {asset_symbol}: {str(exc)}")
        try:
            raise self.retry(countdown=60, exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for {asset_symbol}")
            return f"Failed to fetch data for {asset_symbol}"

@shared_task
def calculate_asset_indicators(asset_symbol):
    """
    Calculate basic technical indicators for an asset
    """
    try:
        asset = Asset.objects.get(symbol=asset_symbol)
        market_data = MarketData.objects.filter(asset=asset).order_by('timestamp')

        if not market_data.exists():
            logger.warning(f"No market data found for {asset_symbol}")
            return

        # Convert to DataFrame for calculations
        df = pd.DataFrame(list(market_data.values('timestamp', 'close', 'volume')))
        df.set_index('timestamp', inplace=True)

        # Calculate basic indicators
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std()

        # Save calculated indicators back to database
        for timestamp, row in df.iterrows():
            if pd.notna(row['returns']):
                MarketData.objects.filter(asset=asset, timestamp=timestamp).update(
                    returns=float(row['returns']) if pd.notna(row['returns']) else None,
                    volatility=float(row['volatility']) if pd.notna(row['volatility']) else None
                )

        logger.info(f"Calculated indicators for {asset_symbol}")

        # Trigger quantum analysis
        from prediction.tasks import queue_quantum_analysis
        queue_quantum_analysis.delay(asset_symbol)

    except Asset.DoesNotExist:
        logger.error(f"Asset {asset_symbol} not found")
    except Exception as e:
        logger.error(f"Error calculating indicators for {asset_symbol}: {str(e)}")

@shared_task
def update_all_assets_data():
    """
    Batch update market data for all active assets
    """
    active_assets = Asset.objects.filter(is_active=True)

    # Create a group of tasks for parallel execution
    job = group(fetch_market_data.s(asset.symbol) for asset in active_assets)
    result = job.apply_async()

    logger.info(f"Started market data update for {active_assets.count()} assets")
    return f"Update initiated for {active_assets.count()} assets"