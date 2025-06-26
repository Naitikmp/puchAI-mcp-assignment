import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TOKEN")
MY_NUMBER = os.getenv("MY_NUMBER")
RESUME_FILE = "resume.md"