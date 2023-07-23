import asyncio
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from starlette.middleware.cors import CORSMiddleware
from datetime import timedelta

from app.utils import StudentsDataFetcher, get_latest_dump_date, get_utc_date
from app.calculations import MainPageCalculations

origins = ["https://pk23.dvfu.ru", "*"]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

main_page_data: dict | None = None


@app.on_event("startup")
@repeat_every(seconds=60*90, wait_first=False)
async def update_main_page():
    cur_time = await get_utc_date()
    last_dump_date = await get_latest_dump_date()
    if last_dump_date is not None and last_dump_date + timedelta(hours=2) > cur_time:
        print("Dump is fresh. Continue...")
        return
    fetcher = StudentsDataFetcher()
    await fetcher.fetch_and_dump_students_data()
    await asyncio.sleep(30)
    global main_page_data
    print('Initializing main page calculations...')
    calc = MainPageCalculations()
    print('Calculating main page data...')
    main_page_data = await calc.get_main_page_data()


@app.get("/main_page")
async def main_page():
    global main_page_data
    if main_page_data is None:
        print('Initializing main page calculations...')
        calc = MainPageCalculations()
        print('Calculating main page data...')
        main_page_data = await calc.get_main_page_data()
    return main_page_data
