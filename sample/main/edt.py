import asyncio
import base64
import datetime

import discord
from PIL import Image
from io import BytesIO

import fetch as _fetch

edt_available = {'l3info', 'l3miage', 'm1miage', 'm1info', 'm2miage'}
one_week = datetime.timedelta(days=7)


async def get_edt(date_edt, nb_day, cursus):
    width = nb_day * 160  # ou 144
    day_str = "0,1,2,3,4,5"
    payload = {'idPianoWeek': date_edt, 'idPianoDay': day_str, 'height': '720', 'width': width}
    my_url = 'http://www.emploisdutemps.fr/image/get/' + cursus
    data = await _fetch.fetch_data_post_json(my_url, payload)
    if data == -1:
        return -1
    else:
        return Image.open(BytesIO(base64.b64decode(data['img'])))


async def send_edt(ctx, cursus, date=datetime.date.today()):
    cursus = cursus.split(None, 1)[0]
    if cursus not in edt_available:
        await ctx.send(content="Cet emploi du temps n'est pas disponible sur le bot.\nEmplois du temps disponibles :\n"
                               "{}".format(", ".join(str(i) for i in sorted(edt_available))))
        return -1

    edt = await get_edt(date.strftime("%Y-%m-%d"), 6, cursus)
    if edt == -1:
        await ctx.send("Échec de la récupération de l'emploi du temps sur <www.emploisdutemps.fr>.")
    else:
        imgbytes = BytesIO()
        edt.save(imgbytes, format='PNG')
        msg_sent = await ctx.channel.send(file=discord.File(imgbytes.getvalue(), "edt.png"))
        await msg_sent.add_reaction(emoji='⏪')
        await msg_sent.add_reaction(emoji='⏩')

        def checkreactionedt(reaction, user):
            return user != ctx.bot.user and msg_sent.id == reaction.message.id \
                   and (str(reaction.emoji == '⏪' or str(reaction.emoji == '⏩')))

        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=15.0, check=checkreactionedt)
        except asyncio.TimeoutError:
            pass
            await msg_sent.remove_reaction(emoji='⏪', member=msg_sent.author)
            await msg_sent.remove_reaction(emoji='⏩', member=msg_sent.author)
        else:
            if reaction.emoji == '⏪':
                date = date - one_week
            elif reaction.emoji == '⏩':
                date = date + one_week
            await msg_sent.delete()
            await send_edt(ctx, cursus, date)
