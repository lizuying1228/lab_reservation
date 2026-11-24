
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

BASE_URL = "http://127.0.0.1:8001/api"

TOKEN_A = os.environ["TOKEN_A"]
TOKEN_B = os.environ["TOKEN_B"]

RESERVATION_TIME_ID = 78

barrier = Barrier(2)

def submit(token, student):
    barrier.wait()

    request = Request(
        f"{BASE_URL}/reservations/",
        data=f'{{"reservationtime_id":{RESERVATION_TIME_ID}}}'.encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request) as response:
            result = response.read().decode()
            print(f"{student}: {response.status} {result}")
    except HTTPError as e:
        print(f"{student}: {e.code} {e.read().decode()}")

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [
        executor.submit(submit, TOKEN_A, "学生 A"),
        executor.submit(submit, TOKEN_B, "学生 B"),
    ]

    for future in futures:
        future.result()

