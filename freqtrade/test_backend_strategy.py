import json
import pytest
from datetime import datetime
from backend_strategy import BackendStrategy
from pathlib import Path

class DummyTrade:
    def __init__(self, enter_tag):
        self.enter_tag = enter_tag

@pytest.fixture
def strategy():
    config_path = Path("config.json")
    with config_path.open() as f:
        config = json.load(f)
    return BackendStrategy(config)

def test_custom_entry_price_long(strategy):
    tag = '{"price": 105.0}'
    result = strategy.custom_entry_price(
        pair="BTC/USDT",
        trade=None,
        current_time=datetime.now(),
        proposed_rate=100.0,
        entry_tag=tag,
        side="long"
    )
    assert result == 100.0

def test_custom_entry_price_short(strategy):
    tag = '{"price": 95.0}'
    result = strategy.custom_entry_price(
        pair="BTC/USDT",
        trade=None,
        current_time=datetime.now(),
        proposed_rate=100.0,
        entry_tag=tag,
        side="short"
    )
    assert result == 100.0

def test_custom_entry_price_valid(strategy):
    tag = '{"price": 98.0}'
    result = strategy.custom_entry_price(
        pair="BTC/USDT",
        trade=None,
        current_time=datetime.now(),
        proposed_rate=100.0,
        entry_tag=tag,
        side="long"
    )
    assert result == 98.0

def test_custom_stoploss_valid_tag(strategy):
    trade = DummyTrade(enter_tag=json.dumps({"stoploss": 2.5}))
    result = strategy.custom_stoploss(
        pair="BTC/USDT",
        trade=trade,
        current_time=datetime.now(),
        current_rate=10000,
        current_profit=0.02,
        after_fill=True
    )
    assert result == -0.025

def test_custom_stoploss_no_tag_or_not_after_fill(strategy):
    trade = DummyTrade(enter_tag=json.dumps({"stoploss": 2.5}))

    result = strategy.custom_stoploss(
        pair="BTC/USDT",
        trade=trade,
        current_time=datetime.now(),
        current_rate=10000,
        current_profit=0.02,
        after_fill=False # <- Important difference
    )
    assert result is None

def test_custom_exit_target_reached(strategy):
    trade = DummyTrade(enter_tag=json.dumps({"takeProfit": 5})) # 5%
    result = strategy.custom_exit(
        pair="BTC/USDT",
        trade=trade,
        current_time=datetime.now(),
        current_rate=10000,
        current_profit=0.06 # 6% profit
    )
    assert result is True # Trade to be terminated

def test_custom_exit_target_not_reached(strategy):
    trade = DummyTrade(enter_tag=json.dumps({"takeProfit": 5})) # 5%
    result = strategy.custom_exit(
        pair="BTC/USDT",
        trade=trade,
        current_time=datetime.now(),
        current_rate=10000,
        current_profit=0.03 # 3% profit
    )
    assert result is False # Trade to continue
