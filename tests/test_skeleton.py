def test_import_backtester():
    from cs2_trading.backtest.backtester import Backtester

    bt = Backtester()
    assert bt is not None
