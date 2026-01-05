import requests


def test_request_energycharts():
    api_url = "https://api.energy-charts.info/ren_share_forecast?country=de"
    headers = {
        "accept": "application/json",
        "User-Agent": "Erneuerbare Energien Überschuss Mastobot",
    }
    r = requests.get(api_url, headers=headers)
    r.raise_for_status()
    assert r.status_code == 200
