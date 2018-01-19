import locale
import re
from datetime import date
from bs4 import SoupStrainer, BeautifulSoup

import discord
import logging
import config
import aiohttp

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='../bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

locale.setlocale(locale.LC_ALL, 'fr-FR')

client = discord.Client(game=discord.Game(type=3, name="Chackal"))
# 0 : Joue à , 1 : , 2 : Écoute, 3 : Regarde

_menu = discord.Embed()
_menu.type = "rich"
_menu.title = "Resto’ U de l’Illberg"
_menu.url = "http://www.crous-strasbourg.fr/restaurant/resto-u-de-lillberg/"
_menu.colour = discord.Colour.red()


async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://www.crous-strasbourg.fr/restaurant/resto-u-de-lillberg/') as r:
            if r.status == 200:
                ss = SoupStrainer(id="menu-repas")
                return BeautifulSoup(await r.text(), "html.parser", parse_only=ss)
            else:
                return -1


async def get_menu():
    today = date.today().strftime("Menu du %A %d %B %Y")
    if _menu.description == today:
        return _menu
    else:
        _menu.description = today
        temp = await fetch_data()
        if temp == -1:
            return "Connection error"
        temp = temp.find("h3", string=re.compile(today)).next_element.next_element.next_element
        temp = temp.find("h4", string=re.compile("Déjeuner")).next_element.next_element.next_element

        for t in temp.find_all('span'):
            name = t.text.strip()
            value = ""
            t2 = t.next_element.next_element
            for t3 in t2.find_all("li"):
                value += t3.text.strip() + "\n"

            _menu.add_field(name=name, value=value, inline=False)

        return _menu


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$ru'):
        menu = await get_menu()
        await message.channel.send(embed=menu)


client.run(config.discord_token)
