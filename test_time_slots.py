import euemastobot as bot
import json


def test_timeslot_without_threshold():
    forecast = _create_forecast_object([50, 60, 30])
    result = bot.get_slots_from_forecast(forecast)
    assert len(result) == 0


def test_timeslot_with_threshold():
    forecast = _create_forecast_object([50, 110, 30])
    result = bot.get_slots_from_forecast(forecast)
    print(result)
    assert len(result) == 1


def test_timeslot_with_threshold_100():
    forecast = _create_forecast_object([50, 100, 30])
    result = bot.get_slots_from_forecast(forecast)
    print(result)
    assert len(result) == 0


def test_timeslot_with_two_slots():
    forecast = _create_forecast_object([50, 110, 20, 130, 30])
    result = bot.get_slots_from_forecast(forecast)
    print(result)
    assert len(result) == 2


def test_timeslot_with_threshold_at_start():
    forecast = _create_forecast_object([110, 20, 30, 30])
    result = bot.get_slots_from_forecast(forecast)
    print(result)
    assert len(result) == 1


def test_timeslot_with_threshold_at_end():
    forecast = _create_forecast_object([30, 20, 30, 30, 110])
    result = bot.get_slots_from_forecast(forecast)
    print(result)
    assert len(result) == 1


def test_timeslot_with_threshold_at_start_and_end():
    forecast = _create_forecast_object([110, 20, 30, 30, 110])
    result = bot.get_slots_from_forecast(forecast)
    print(result)
    assert len(result) == 2


def test_real_forecasts_from_api_whole_day():
    with open("test_data/whole_day_above_threshold.json", "r") as file:
        forecast = json.load(file)
        slots = bot.get_slots_from_forecast(forecast)
        assert len(slots) == 1


def test_real_forecasts_from_api_two_slots():
    with open("test_data/two_slots_ending_the_day.json", "r") as file:
        forecast = json.load(file)
        slots = bot.get_slots_from_forecast(forecast)
        assert len(slots) == 2


def _create_forecast_object(percentages):
    # skipping objects solar_share, wind_onshore_share and wind_offshore_share
    # Unix seconds resolution is 900
    timestamp_start = 1734735600
    result = {
        "unix_seconds": [x * 900 + timestamp_start for x in range(0, len(percentages))],
        "ren_share": percentages,
        "substitute": False,
        "deprecated": False,
    }
    return result
