import requests
import logging
import json
from datetime import datetime
from pandas import DataFrame
from freqtrade.strategy.interface import IStrategy
from freqtrade.persistence import Trade

logger = logging.getLogger(__name__)

class BackendStrategy(IStrategy):

    # URL of the external trade signal server
    external_server_url = "http://trading-server:3000/api/v1/trading/tradePlan"

    # Enable short trading
    can_short: bool = True

    # Enable custom stoploss
    use_custom_stoploss = True

    # disable trailing stop if using custom stoploss
    trailing_stop = False

    # Maximum loss before stopping out
    stoploss = -0.05

    # Trading timeframe
    timeframe = '5m'

    # Minimum return on investment (ROI)
    minimal_roi = {
        "0": 0.10
    }

    def is_trade_active(self, pair: str) -> bool:
        """
        Determines if there is an open trade for trading pair.
        """
        open_trades = Trade.get_open_trades()
        return any(trade for trade in open_trades if trade.pair == pair)


    def send_trade_signal(self, metadata: list) -> dict:
        """
        Sends a trade signal request to an external server.
        """
        if self.is_trade_active(metadata['pair']):
            logger.info(f"There is already an open trade for {metadata['pair']}")
            return None

        exchange_name = self.config.get("exchange", {}).get("name")

        payload = {
            "exchange": exchange_name,
            "pair": metadata['pair'],
            "timeframe": self.timeframe
        }
        headers = {}
        # headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            # TODO: set timeout
            # Sending POST request to the external server
            response = requests.post(self.external_server_url, json=payload, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            response_data = response.json()
            logger.info(f"trade signal from backend: {response_data}")
            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending signal:{e}")
            return None


    def leverage(self, pair: str, current_time: datetime, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str | None, side: str,
                 **kwargs) -> float:
        """
        Customize leverage for each new trade. This method is only called in futures mode.

        :param pair: Pair that's currently analyzed
        :param current_time: datetime object, containing the current datetime
        :param current_rate: Rate, calculated based on pricing settings in exit_pricing.
        :param proposed_leverage: A leverage proposed by the bot.
        :param max_leverage: Max leverage allowed on this pair
        :param entry_tag: Optional entry_tag (buy_tag) if provided with the buy signal.
        :param side: "long" or "short" - indicating the direction of the proposed trade
        :return: A leverage amount, which is between 1.0 and max_leverage.
        """
        if entry_tag:
            try:
                tag_data = json.loads(entry_tag)
                custom_leverage = float(tag_data.get("leverage", proposed_leverage))
            except Exception as e:
                logger.error(f"Error parsing leverage entry_tag: {e}")
                custom_leverage = proposed_leverage
        else:
            logger.warning("leverage entry_tag not set")
            custom_leverage = proposed_leverage

        return min(custom_leverage, max_leverage)


    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, after_fill: bool,
                        **kwargs) -> float | None:
        """
        Custom stoploss logic, returning the new distance relative to current_rate (as ratio).
        e.g. returning -0.05 would create a stoploss 5% below current_rate.
        The custom stoploss can never be below self.stoploss, which serves as a hard maximum loss.

        When not implemented by a strategy, returns the initial stoploss value.
        Only called when use_custom_stoploss is set to True.

        :param pair: Pair that's currently analyzed
        :param trade: trade object.
        :param current_time: datetime object, containing the current datetime
        :param current_rate: Rate, calculated based on pricing settings in exit_pricing.
        :param current_profit: Current profit (as ratio), calculated based on current_rate.
        :param after_fill: True if the stoploss is called after the order was filled.
        :param **kwargs: Ensure to keep this here so updates to this won't break your strategy.
        :return float: New stoploss value, relative to the current_rate
        """
        if after_fill and trade.enter_tag:
            try:
                tag_data = json.loads(trade.enter_tag)
                sl = tag_data.get("stoploss")
                if sl is not None:
                    val = float(sl)
                    # Maximum SL in percent from self.stoploss (e.g. -0.05 -> 5.0)
                    max_sl_pct = abs(self.stoploss) * 100.0
                    # Only normalize if val > max_sl_pct
                    if val > max_sl_pct:
                        # If decimal places, limit directly to max.
                        if not val.is_integer():
                            val = max_sl_pct
                        else:
                            # Integer: divide by the appropriate power of 10
                            digits = len(str(int(val)))
                            corrected = val / (10 ** (digits - 1))
                            val = corrected if corrected <= max_sl_pct else max_sl_pct
                    # Round cleanly to 4 decimal places in percent fractions
                    stop_pct = round(val / 100.0, 4)
                    return -stop_pct
            except Exception as e:
                logger.error(f"Error parsing trade.enter_tag: {e}")

        return None


    def custom_entry_price(self, pair: str, trade: Trade | None, current_time: datetime, proposed_rate: float,
                           entry_tag: str | None, side: str, **kwargs) -> float:
        """
        Custom entry price.
        """
        if entry_tag:
            try:
                tag_data = json.loads(entry_tag)
                entry_price = float(tag_data.get("price", proposed_rate))
                if side == "long" and entry_price > proposed_rate:
                    entry_price = proposed_rate
                elif side == "short" and entry_price < proposed_rate:
                    entry_price = proposed_rate
            except Exception as e:
                logger.error(f"Error parsing price entry_tag: {e}")
                entry_price = proposed_rate
        else:
            logger.warning("price entry_tag not set")
            entry_price = proposed_rate

        return entry_price


    def custom_exit(self, pair: str, trade: 'Trade', current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs) -> bool:
        """
        Closes the trade individually based on the "takeProfit" value from the trade.enter_tag
        """
        target_roi = None

        if trade.enter_tag:
            try:
                tag_data = json.loads(trade.enter_tag)
                target_roi = tag_data.get("takeProfit")
            except Exception as e:
                logger.error(f"Error parsing enter_tag: {e}")

        if target_roi is not None:
            # If the current profit is greater than or equal to target_roi, close the trade
            if current_profit >= (target_roi / 100):
                return True

        return False


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        A placeholder method for populating indicators.
        """
        #dataframe['rsi_period_14_close'] = ta.RSI(dataframe, timeperiod=14, price='close')
        #dataframe['sma_period_20_close'] = ta.SMA(dataframe, timeperiod=20, price='close')
        #dataframe['sma_period_50_close'] = ta.SMA(dataframe, timeperiod=50, price='close')
        return dataframe


    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Determines entry signals based on external trade signals.
        """

        # Initialize entry signal columns
        dataframe['enter_long'] = 0
        dataframe['enter_short'] = 0

        signal = self.send_trade_signal(metadata)
        if signal is None:
            return dataframe

        tag = json.dumps({
            "id": signal.get('id'),
            "price": signal.get('entryPoint'),
            "stoploss": signal.get("stoploss"),
            "takeProfit": signal.get("takeProfit"),
            "leverage": signal.get("leverage"),
            "pos": signal.get("probabilityOfSuccess")
        })

        if signal.get('direction') == "long":
            dataframe.loc[dataframe.index[-1], ['enter_long', 'enter_tag']] = (1, tag)
        elif signal.get('direction') == "short":
            dataframe.loc[dataframe.index[-1], ['enter_short', 'enter_tag']] = (1, tag)

        return dataframe


    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Determines exit signals. Currently, no exit logic is implemented.
        """

        # Initialize exit signal columns
        dataframe['exit_long'] = 0
        dataframe['exit_short'] = 0

        return dataframe
