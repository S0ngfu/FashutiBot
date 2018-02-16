import asyncio
import locale
import re
import datetime
from bs4 import SoupStrainer, BeautifulSoup
from PIL import Image
from io import BytesIO
import base64
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
fashuti_bot = discord.Client(game=discord.Game(type=3, name="Chackal"))
# 0 : Joue à , 1 : , 2 : Écoute, 3 : Regarde
one_day = datetime.timedelta(days=1)
one_week = datetime.timedelta(days=7)

_menu = {
    "embed": discord.Embed(),
    "yesterday": False,
    "tomorrow": False
}
_menu["embed"].type = "rich"
_menu["embed"].title = "Resto’ U de l’Illberg"
_menu["embed"].url = "http://www.crous-strasbourg.fr/restaurant/resto-u-de-lillberg/"
_menu["embed"].colour = discord.Colour.red()


async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                return await r.text()
            else:
                return -1


async def fetch_data_post_json(url, payload):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as r:
            if r.status == 200:
                return await r.json()
            else:
                return -1


async def get_menu(date):
    today = date.strftime("Menu du %A {0} %B %Y").format(date.day)
    temp_day = date-one_day
    yesterday = temp_day.strftime("Menu du %A {0} %B %Y").format(temp_day.day)
    temp_day = date+one_day
    tomorrow = temp_day.strftime("Menu du %A {0} %B %Y").format(temp_day.day)
    _menu["embed"].clear_fields()
    html = await fetch_data('http://www.crous-strasbourg.fr/restaurant/resto-u-de-lillberg/')
    if html == -1:
        return "Erreur de connexion"
    else:
        html = BeautifulSoup(html, "html.parser", parse_only=SoupStrainer(id="menu-repas"))

    if html.find("h3", string=re.compile(today)) is None:
        return today + " non trouvé."

    if html.find("h3", string=re.compile(yesterday)) is None:
        _menu["yesterday"] = False
    else:
        _menu["yesterday"] = True

    if html.find("h3", string=re.compile(tomorrow)) is None:
        _menu["tomorrow"] = False
    else:
        _menu["tomorrow"] = True

    html = html.find("h3", string=re.compile(today)).next_element.next_element.next_element
    html = html.find("h4", string=re.compile("Déjeuner")).next_element.next_element.next_element
    _menu["embed"].description = today
    for t in html.find_all('span'):
        name = t.text.strip()
        value = ""
        t2 = t.next_element.next_element
        for t3 in t2.find_all("li"):
            value += t3.text.strip() + "\n"

        _menu["embed"].add_field(name=name, value=value, inline=False)

    return _menu


async def get_edt(date_edt, nb_day, a):
    width = nb_day * 160  # ou 144
    day_str = "0,1,2,3,4,5"
    payload = {'idPianoWeek': date_edt, 'idPianoDay': day_str, 'height': '720', 'width': width}
    my_url = 'http://www.emploisdutemps.fr/image/get/' + a
    data = await fetch_data_post_json(my_url, payload)
    if data == -1:
        return "Erreur de connexion"
    else:
        return Image.open(BytesIO(base64.b64decode(data['img'])))


async def send_menu(message, today):
    menu = await get_menu(today)
    if isinstance(menu, str):
        await message.channel.send(menu)
    else:
        msg_sent = await message.channel.send(embed=menu["embed"])
        if menu["yesterday"]:
            await msg_sent.add_reaction(emoji='⏪')
        if menu["tomorrow"]:
            await msg_sent.add_reaction(emoji='⏩')

        def checkreactionru(reaction, user, yesterday=menu["yesterday"], tomorrow=menu["tomorrow"]):
            tmp_bool = False
            if yesterday and str(reaction.emoji) == '⏪':
                tmp_bool = True
            if tomorrow and str(reaction.emoji) == '⏩':
                tmp_bool = True
            return user == message.author and msg_sent.id == reaction.message.id and tmp_bool

        try:
            reaction, user = await fashuti_bot.wait_for('reaction_add',
                                                        timeout=10.0,
                                                        check=checkreactionru)
        except asyncio.TimeoutError:
            pass
            # ToDo : delete the reaction (no more usable)
        else:
            if reaction.emoji == '⏪':
                today = today - one_day
                menu = await get_menu(today)
                if isinstance(menu, str):
                    await msg_sent.edit(menu, embed=None)
                else:
                    await msg_sent.edit(embed=menu["embed"])
                    if menu["yesterday"]:
                        await msg_sent.add_reaction(emoji='⏪')
                    if menu["tomorrow"]:
                        await msg_sent.add_reaction(emoji='⏩')
            elif reaction.emoji == '⏩':
                today = today + one_day
                menu = await get_menu(today)
                if isinstance(menu, str):
                    await msg_sent.edit(menu, embed=None)
                else:
                    await msg_sent.edit(embed=menu["embed"])
                    if menu["yesterday"]:
                        await msg_sent.add_reaction(emoji='⏪')
                    if menu["tomorrow"]:
                        await msg_sent.add_reaction(emoji='⏩')


@fashuti_bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(fashuti_bot))


# chackal id : 131187030628630530
@fashuti_bot.event
async def on_member_update(before, after):
    if before.id == 131187030628630530:
        if after.game is not None:
            if after.game.type == 1:
                await fashuti_bot.change_presence(game=discord.Game(name=after.game.name,
                                                                    url=after.game.url,
                                                                    type=after.game.type))
            else:
                await fashuti_bot.change_presence(game=discord.Game(type=3,
                                                                    name="Chackal joué à {0.name}".format(after.game)))
        else:
            if after.status == discord.Status.online:
                await fashuti_bot.change_presence(game=discord.Game(type=3,
                                                                    name="Chackal"))
            if after.status == discord.Status.idle:
                await fashuti_bot.change_presence(game=discord.Game(type=3,
                                                                    name="Chackal manger"))
            if after.status == discord.Status.dnd:
                await fashuti_bot.change_presence(game=discord.Game(type=3,
                                                                    name="Chackal chier"))
            if after.status == discord.Status.offline:
                await fashuti_bot.change_presence(game=discord.Game(type=3,
                                                                    name="Chackal dormir"))


@fashuti_bot.event
async def on_message(message):
    if message.author == fashuti_bot.user:
        return

    if message.content.startswith('$ru'):
        today = datetime.date.today()
        await send_menu(message, today)

    elif message.content.startswith('$edt'):
        # parse arguments and give it to get_edt
        nb = 6  # all week
        date_edt = datetime.date.today()

        if message.content.find('info') != -1:
            azertyuiop = "m1info"
        else:
            azertyuiop = "m1miage"

        if date_edt:
            edt = await get_edt(date_edt.strftime("%Y-%m-%d"), nb, azertyuiop)
            if isinstance(edt, str):
                await message.channel.send("Échec de la récupération de l'emploi du temps sur "
                                           "<www.emploisdutemps.fr>.")
            else:
                imgbytes = BytesIO()
                edt.save(imgbytes, format='PNG')
                msg_sent = await message.channel.send(file=discord.File(imgbytes.getvalue(), 'edt.png'))

                await msg_sent.add_reaction(emoji='⏪')
                await msg_sent.add_reaction(emoji='⏩')

                def checkreactionedt(reaction, user):
                    return user == message.author and (str(reaction.emoji) == '⏪' or str(reaction.emoji) == '⏩')

                try:
                    reaction, user = await fashuti_bot.wait_for('reaction_add', timeout=10.0, check=checkreactionedt)
                except asyncio.TimeoutError:
                    pass
                    # ToDo : delete the reaction (no more usable)
                else:
                    if reaction.emoji == '⏪':
                        date_edt = date_edt - one_week
                    elif reaction.emoji == '⏩':
                        date_edt = date_edt + one_week
                    edt = await get_edt(date_edt.strftime("%Y-%m-%d"), nb, azertyuiop)
                    if isinstance(edt, str):
                        await msg_sent.channel.send("Échec de la récupération de l'emploi du temps sur "
                                                    "<www.emploisdutemps.fr>.")
                        await msg_sent.delete()
                    else:
                        imgbytes = BytesIO()
                        edt.save(imgbytes, format='PNG')
                        await msg_sent.channel.send(file=discord.File(imgbytes.getvalue(), 'edt.png'))
                        await msg_sent.delete()

    # message.embeds : list of embeds + attachments

fashuti_bot.run(config.dev_token)
