from datetime import datetime
from mastodon import Mastodon
import dotenv
import logging
import os
import requests
import asyncio
from playwright.async_api import async_playwright
import locale

threshold = 100
mastodon = None


def get_slots_from_forecast(forecast):
    i = 0
    filter_above_threshold = []
    for row in forecast["ren_share"]:
        if row > threshold:
            filter_above_threshold.append(1)
        else:
            filter_above_threshold.append(0)
        i += 1
    logging.debug("Above threshold: ")
    logging.debug(filter_above_threshold)
    start = 0
    previous = 0
    slots = []
    i = 0
    added = True
    for time_slice in filter_above_threshold:
        if time_slice != previous:
            previous = time_slice
            if time_slice == 1:
                start = forecast["unix_seconds"][i]
                added = False
            elif time_slice == 0:
                end = forecast["unix_seconds"][i - 1]
                start_text = datetime.fromtimestamp(start).strftime("%H:%M")
                end_text = datetime.fromtimestamp(end).strftime("%H:%M")
                slots.append((start_text, end_text))
                added = True
        i += 1

    # If the threshold was exceeded at the end, has it been added to the array yet?
    if not added:
        start_text = datetime.fromtimestamp(start).strftime("%H:%M")
        end_text = "00:00"
        slots.append((start_text, end_text))
    return slots


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

    slots = get_slots_from_forecast(forecast)

    return slots


def get_mastodon_client():
    global mastodon
    if mastodon is None:
        logger.info("Create new Mastodon client")
        mastodon = Mastodon(
            api_base_url="https://ruhr.social",
            access_token=os.getenv("ACCESS_TOKEN"),
        )
    return mastodon


def post_timeslots_to_mastodon(time_slots, attach_screenshot=False, media_id=None):
    mastodon = get_mastodon_client()
    day_of_week = datetime.today().strftime("%A")
    slot_text = ", ".join(["{} - {}".format(slot[0], slot[1]) for slot in time_slots])
    status_text = """Am heutigen {} liegt zwischen zwischen {} der Anteil der erneuerbaren Energien in Deutschland voraussichtlich über {}%.

Daten via https://energy-charts.info/charts/consumption_advice/chart.htm""".format(
        day_of_week, slot_text, threshold
    )
    logger.debug(status_text)
    status = mastodon.status_post(status_text, language="de", media_ids=media_id)
    logger.info("Posted status #{} ({})".format(status["id"], status["created_at"]))
    return status["url"]


async def create_screenshot_of_traffic_light():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(locale="de-DE")
        await page.set_viewport_size({"width": 765, "height": 500})
        await page.goto(
            "https://energy-charts.info/charts/consumption_advice/chart.htm?l=de&c=DE"
        )
        await page.locator("div#inhalt .chartCard:first-child").screenshot(
            path="stromampel.png"
        )
        await browser.close()
    logger.info("Created screenshot")
    mastodon = get_mastodon_client()
    result = mastodon.media_post(
        "stromampel.png",
        description="Screenshot of energy-charts.info"
        "s traffic light for energy production",
        file_name="Stromampel.png",
    )
    logger.info("Uploaded screenshot with ID {}".format(result["id"]))
    return result["id"]


if __name__ == "__main__":
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    date_format = "%d.%m. %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt=date_format)
    logger = logging.getLogger("euemastobot")

    locale.setlocale(locale.LC_TIME, "de_DE") 

    time_slots = None
    try:
        time_slots = get_time_slots()
    except Exception as e:
        logger.exception("Could not get forecast data", e)

    if time_slots is not None:
        if len(time_slots) == 0:
            logger.info(
                "No time slots with energy above threshold of {}% found".format(
                    threshold
                )
            )
        else:
            dotenv.load_dotenv()
            media_id = None
            try:
                media_id = asyncio.run(create_screenshot_of_traffic_light())
            except Exception as e:
                logger.error("Could not create screenshot", e)
            post_url = post_timeslots_to_mastodon(time_slots, media_id=media_id)
            logger.info("Successfully posted: {}".format(post_url))
