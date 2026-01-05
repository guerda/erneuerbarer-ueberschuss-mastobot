import euemastobot as bot
from test_time_slots import _create_forecast_object


def test_chart():
    forecast_object = _create_forecast_object([i for i in range(1, 100)])
    bot.create_chart(forecast_object)
