import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Configuration
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "")

# Firebase Configuration (export as JSON string or use service account file)
FIREBASE_SERVICE_ACCOUNT = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")

# Admin Configuration
ADMIN_USER_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_USER_IDS", "").split(",") if x.strip()]

# Database Collections
USERS_COLLECTION = "users"
GROUPS_COLLECTION = "groups"
TRANSACTIONS_COLLECTION = "transactions"
