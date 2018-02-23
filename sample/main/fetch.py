import aiohttp
import datetime

last_ru_update = datetime.datetime.today() - datetime.timedelta(hours=2)


async def fetch_data_get_text(url):
    global last_ru_update
    if datetime.datetime.today() - last_ru_update > datetime.timedelta(hours=1):
        last_ru_update = datetime.datetime.today()
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                if r.status == 200:
                    return await r.text()
                else:
                    return -1
    return -1


async def fetch_data_post_json(url, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as r:
            if r.status == 200:
                return await r.json()
            else:
                return -1
