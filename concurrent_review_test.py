
import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

BASE_URL = "http://127.0.0.1:8001/api"
TOKEN = os.environ["ADMIN_TOKEN"]

RESERVATION_IDS = [29, 30]
barrier = Barrier(2)

def approve(reservation_id):
    barrier.wait()

    request = Request(
        f"{BASE_URL}/reservations/{reservation_id}/review/",
        data=json.dumps({"status": "approved"}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        method="PATCH",
    )

    try:
        with urlopen(request) as response:
            print(reservation_id, response.status, response.read().decode())
    except HTTPError as e:
        print(reservation_id, e.code, e.read().decode())

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [
        executor.submit(approve, reservation_id)
        for reservation_id in RESERVATION_IDS
    ]
    for future in futures:
        future.result()
