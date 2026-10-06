import locale
import logging
import os
from datetime import datetime

import dotenv
import pygal
import requests
from mastodon import Mastodon
from pygal.style import *
from python_ntfy import NtfyClient

threshold = 100
mastodon = None
logger = logging.getLogger("euemastobot")
# Determine local timezone
now = datetime.now()  # noqa: DTZ005
local_now = now.astimezone()
local_tz = local_now.tzinfo


def get_slots_from_forecast(forecast):
    filter_above_threshold = []
    slot_count = 0

    for i, row in enumerate(forecast["ren_share"]):
        if row > threshold:
            filter_above_threshold.append(1)
            slot_count += 1
        else:
            filter_above_threshold.append(0)
    logger.info(f"Hours above threshold: {slot_count / 4}")
    logger.debug("Above threshold: ")
    logger.debug(filter_above_threshold)
    start = 0
    previous = 0
    slots = []
    i = 0
    added = True
    for i, time_slice in enumerate(filter_above_threshold):
        if time_slice != previous:
            previous = time_slice
            if time_slice == 1:
                start = forecast["unix_seconds"][i]
                added = False
            elif time_slice == 0:
                end = forecast["unix_seconds"][i - 1]
                start_text = datetime.fromtimestamp(start, tz=local_tz).strftime(
                    "%H:%M"
                )
                end_text = datetime.fromtimestamp(end, tz=local_tz).strftime("%H:%M")
                slots.append((start_text, end_text))
                added = True

    # If the threshold was exceeded at the end, has it been added to the array yet?
    if not added:
        start_text = datetime.fromtimestamp(start, tz=local_tz).strftime("%H:%M")
        end_text = "00:00"
        slots.append((start_text, end_text))
    return slots, slot_count - 1  # one slot less to calculate the hours


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

    slots, count_of_slots = get_slots_from_forecast(forecast)

    return slots, count_of_slots, forecast


def get_mastodon_client():
    global mastodon
    if mastodon is None:
        logger.info("Create new Mastodon client")
        mastodon = Mastodon(
            api_base_url="https://ruhr.social",
            access_token=os.getenv("ACCESS_TOKEN"),
        )
    return mastodon


def post_timeslots_to_mastodon(
    time_slots,
    attach_screenshot=False,
    media_id=None,
    count_of_slots: int = 0,
    dry_run: bool = False,
):
    mastodon = get_mastodon_client()
    day_of_week = datetime.today().astimezone().strftime("%A")
    slot_text = ", ".join([f"{slot[0]} - {slot[1]}" for slot in time_slots])
    status_text = """Am heutigen {} liegt zwischen {} der Anteil der erneuerbaren Energien in Deutschland voraussichtlich über {}%.
    Das entspricht insgesamt {} Stunden erneuerbarem Überschuss.

Daten via https://energy-charts.info/charts/consumption_advice/chart.htm""".format(
        day_of_week,
        slot_text,
        threshold,
        locale.format_string("%.2f", count_of_slots / 4),
    )
    logger.debug(status_text)
    visibility = "public"
    if dry_run:
        visibility = "direct" # private is for followers only
    status = mastodon.status_post(
        status_text, language="de", media_ids=media_id, visibility=visibility
    )
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


def create_chart(forecast_object):
    chart_file_name = "chart.png"
    series = []
    one_hundred_percent_line = []
    current_day = None
    for i, timestamp in enumerate(forecast_object["unix_seconds"]):
        ts = datetime.fromtimestamp(timestamp, None)
        if current_day is None:
            current_day = ts.date()
        # If the next day comes, abort
        if current_day.day != ts.day:
            break
        series.append((ts, forecast_object["ren_share"][i]))
    # Only append the first and last timestamp to 100% line
    one_hundred_percent_line.append((series[0][0], 100))
    one_hundred_percent_line.append((series[-1][0], 100))

    darken_style = Style(colors=("#15d863", "#083D77"))
    line_chart = pygal.TimeLine(
        x_label_rotation=25,
        legend_at_bottom=True,
        style=darken_style,
        interpolate="cubic",
    )
    line_chart.title = f"Erneuerbarer Überschuss für {current_day}"

    line_chart.add("100%", one_hundred_percent_line, fill=True)
    line_chart.add("Anteil erneuerbarer Energien", series)
    line_chart.render_to_png(chart_file_name)
    logger.info(f"Plotted chart to {chart_file_name}")

    mastodon = get_mastodon_client()
    result = mastodon.media_post(
        chart_file_name,
        description=f"Verlauf des Anteils erneuerbaren Energien für {current_day}",
        file_name="Überschuss erneuerbarer Energien.png",
    )
    logger.info("Uploaded screenshot with ID {}".format(result["id"]))
    return result["id"]


if __name__ == "__main__":
    FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    date_format = "%d.%m. %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt=date_format)

    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
    ntfy = NtfyClient(
        topic="erneuerbarer-ueberschuss", server="https://ntfy.local.guerda.de"
    )

    if logger.getEffectiveLevel() == logging.DEBUG:
        logger.debug("Debug level activated, therefore dry_run activated")
        dry_run = True
    else:
        dry_run = False

    time_slots = None
    count_of_slots = 0
    forecast = None
    try:
        time_slots, count_of_slots, forecast = get_time_slots()
    except Exception:
        msg = "Could not retrieve forecast data"
        logger.exception(msg)
        ntfy.send(msg)

    if time_slots is not None:
        if len(time_slots) == 0:
            logger.info(
                f"No time slots with energy above threshold of {threshold}% found"
            )
        else:
            dotenv.load_dotenv()
            media_id = None
            try:
                media_id = create_chart(forecast)
            except Exception:
                msg = "Could not plot chart"
                logger.exception(msg)
                ntfy.send(msg)
            post_url = post_timeslots_to_mastodon(
                time_slots,
                media_id=media_id,
                count_of_slots=count_of_slots,
                dry_run=dry_run,
            )
            logger.info(f"Successfully posted: {post_url}")
