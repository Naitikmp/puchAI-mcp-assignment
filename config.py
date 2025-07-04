import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TOKEN")
MY_NUMBER = os.getenv("MY_NUMBER")
RESUME_FILE = "resume.md"

BASE_URL = "https://7d7b-182-68-21-186.ngrok-free.app"

FMP_API_KEY = os.getenv("FMP_API_KEY")

STOCK_NEWS_API_KEY = os.getenv("STOCK_NEWS_API_KEY")

ATTESTER_API_KEY = os.getenv("ATTESTER_API_KEY")

CASHFREE_CLIENT_ID = os.getenv("CASHFREE_CLIENT_ID")

CASHFREE_CLIENT_SECRET = os.getenv("CASHFREE_CLIENT_SECRET")

OPENCAGE_API_KEY = os.getenv("OPENCAGE_API_KEY")

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")