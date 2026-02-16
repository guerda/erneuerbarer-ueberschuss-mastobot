from mastodon import Mastodon
import dotenv
import os


def test_mastodon_client():
    dotenv.load_dotenv()
    token = os.getenv("ACCESS_TOKEN")
    assert token is not None
    mastodon = Mastodon(api_base_url="https://ruhr.social", access_token=token)
    assert mastodon.me() is not None
