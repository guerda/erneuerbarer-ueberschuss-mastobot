from mastodon import Mastodon
import dotenv
import os


def test_mastodon_client():
    dotenv.load_dotenv()
    mastodon = Mastodon(
        api_base_url="https://ruhr.social", access_token=os.getenv("ACCESS_TOKEN")
    )
    assert mastodon.me() is not None
