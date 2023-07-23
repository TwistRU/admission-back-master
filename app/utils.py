import os
import aiohttp
import aiofiles
import json
import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path
from aiohttp import BasicAuth
from pytz import timezone, utc
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

env = find_dotenv()
load_dotenv(env)

class StudentsDataFetcher:
    URL = os.environ.get('URL')
    HEADERS = {
        'Content-Type': 'application/xml',
    }
    AUTH = BasicAuth(os.environ.get('LOGIN'), os.environ.get('PASSWORD'))
    BODY = '<?xml version="1.0" encoding="utf-8"?><s12:Envelope xmlns:s12=\'http://www.w3.org/2003/05/soap-envelope\'>' \
           + '<s12:Body><ns1:GetStudentsList xmlns:ns1=\'http://www.DVFU_Univer.org\' /></s12:Body></s12:Envelope>'
    LATEST_DUMP_PATH = (Path(os.path.abspath(__file__))).parent.parent / 'data/latest.json'
    DUMPS_DIR = (Path(os.path.abspath(__file__))).parent.parent / 'data/dumps'

    def __init__(self):
        self.fetching_date = None
        pass

    async def fetch_and_dump_students_data(self):

        print('Fetching students data...')
        self.fetching_date = await get_utc_date()
        data_raw = await self._fetch_students_data_raw()
        if data_raw is not None:
            raw_json = ET.fromstring(data_raw)[0][0][0].text

            with open("SAVEFORSCINCE.json", "w") as out:
                out.write(raw_json)
            print('Formatting fetched data...')
            formatted_data = await self._format_raw_json_with_prev(raw_json)
            await asyncio.sleep(2)
            next_dump_number = await self._get_next_dump_number()

            print('Dumping data...')
            async with aiofiles.open(self.LATEST_DUMP_PATH, 'w', encoding='utf-8') as f:
                json_str = json.dumps(formatted_data, ensure_ascii=False)
                await f.write(json_str)
            await asyncio.sleep(10)

            async with aiofiles.open(self.DUMPS_DIR / f'{next_dump_number}.json', 'w', encoding='utf-8') as f:
                json_str = json.dumps(formatted_data, ensure_ascii=False)
                await f.write(json_str)
            print('Done!')

    async def _fetch_students_data_raw(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.URL, headers=self.HEADERS, data=self.BODY, auth=self.AUTH) as resp:
                    response = await resp.text()
                return response
            except Exception as e:
                print(e)

    async def _format_raw_json_with_prev(self, raw_json):
        list_data = json.loads(raw_json)
        prev_data = await self._get_prev_data_or_None()
        date_utc = self.fetching_date
        date_str = date_utc.strftime('%Y-%m-%d %H:%M:%S')
        data = {list_data[i]["Code"]: {} for i in range(len(list_data))}
        for application in list_data:
            key = application["Code"]
            trainingDirection = application["TrainingDirection"]
            data[key][trainingDirection] = application
            if key in prev_data['data']:
                if trainingDirection in prev_data['data'][key]:
                    data[key][trainingDirection]['firstDownloadDate'] = prev_data['data'][key][trainingDirection]['firstDownloadDate']
                else:
                    data[key][trainingDirection]['firstDownloadDate'] = date_str
            else:
                data[key][trainingDirection]['firstDownloadDate'] = date_str

        return {
            'meta': {
                'date': date_str,
            },
            'data': data
        }

    async def _get_prev_data_or_None(self):
        if os.path.exists(self.LATEST_DUMP_PATH):
            async with aiofiles.open(self.LATEST_DUMP_PATH, 'r', encoding='utf-8') as f:
                string = await f.read()
            return json.loads(string)
        return None

    async def _get_next_dump_number(self):
        dumps = sorted([int(i.replace('.json', '')) for i in os.listdir(self.DUMPS_DIR)])
        if len(dumps) == 0:
            return "1"
        else:
            return str(dumps[-1] + 1)


async def get_latest_dump_date():
    print("Getting latest dump date")
    if not StudentsDataFetcher.LATEST_DUMP_PATH.is_file():
        return None
    async with aiofiles.open(StudentsDataFetcher.LATEST_DUMP_PATH, 'r', encoding='utf-8') as f:
        string = await f.read()
    metadata = json.loads(string)['meta']
    date = datetime.strptime(metadata['date'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=utc)
    return date


async def get_local_datetime():
    return datetime.now(tz=timezone('Asia/Vladivostok'))


async def convert_utc_to_local(utc_datetime):
    return utc_datetime.astimezone(timezone('Asia/Vladivostok'))


async def get_utc_date():
    return datetime.now(tz=utc)


async def strptime_to_utc(string, format_):
    return datetime.strptime(string, format_).replace(tzinfo=utc)
