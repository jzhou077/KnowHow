import os
import time

import voyageai
from dotenv import load_dotenv

load_dotenv("/Users/jackz/dev/company-brain/.env")

vo = voyageai.Client(api_key=os.getenv("EMBEDDING_API_KEY"))

for i in range(20):
    try:
        vo.embed([f"test {i}"], model="voyage-4")
        print(f"{i}: ok")
    except Exception as e:
        print(f"{i}: FAILED - {e}")
    time.sleep(0.1)