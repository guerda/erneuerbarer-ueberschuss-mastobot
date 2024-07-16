from datetime import datetime
from mastodon import Mastodon
import dotenv
import logging
import os
import requests

threshold = 100


def get_time_slots():
    api_url = "https://api.energy-charts.info/ren_share_forecast?country=de"
    headers = {
        "accept": "application/json",
        "User-Agent": "Erneuerbare Energien Überschuss Mastobot",
    }
    r = requests.get(api_url, headers=headers)
    r.raise_for_status()
    logger.info("got the forecast data")
    forecast = r.json()

    i = 0
    filter_above_threshold = []
    for row in forecast["ren_share"]:
        if row > threshold:
            filter_above_threshold.append(1)
        else:
            filter_above_threshold.append(0)
        i += 1

    previous = 0
    slots = []
    i = 0
    for time_slice in filter_above_threshold:
        if time_slice != previous:
            previous = time_slice
            if time_slice == 1:
                start = forecast["unix_seconds"][i]
            elif time_slice == 0:
                end = forecast["unix_seconds"][i - 1]
                start_text = datetime.fromtimestamp(start).strftime("%H:%M")
                end_text = datetime.fromtimestamp(end).strftime("%H:%M")
                slots.append((start_text, end_text))
        i += 1

    return slots


def post_timeslots_to_mastodon(time_slots):
    mastodon = Mastodon(
        api_base_url="https://ruhr.social",
        access_token=os.getenv("ACCESS_TOKEN"),
    )
    slot_text = ", ".join(["{} - {}".format(slot[0], slot[1]) for slot in time_slots])
    status_text = """Der Anteil der erneuerbaren Energien in Deutschland liegt voraussichtlich heute zwischen {} über {}%.

Daten via https://energy-charts.info/charts/consumption_advice/chart.htm""".format(
        slot_text, threshold
    )
    status = mastodon.status_post(status_text, language="de")
    logger.info("Posted status #{} ({})".format(status["id"], status["created_at"]))
    return status["url"]


if __name__ == "__main__":
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT)
    logger = logging.getLogger("euemastobot")

    time_slots = None
    try:
        time_slots = get_time_slots()
    except Exception as e:
        logging.exception("Could not get forecast data", e)

    if time_slots is not None:
        if len(time_slots) == 0:
            logger.info(
                "No time slots with energy above threshold of {}% found".format(
                    threshold
                )
            )
        else:
            dotenv.load_dotenv()
            post_url = post_timeslots_to_mastodon(time_slots)
            logger.info("Successfully posted: {}".format(post_url))
