import asyncio
import datetime
import locale
import random
import re

import bs4
import discord

import fetch as _fetch

locale.setlocale(locale.LC_ALL, 'fr_FR')  # fr-FR on windows
_menus = dict()
_menu_url = "http://www.crous-strasbourg.fr/restaurant/resto-u-de-lillberg/"
_menu_type = "rich"
_menu_title = "Resto’ U de l’Illberg"
_menu_colour = discord.Colour.red()
one_day = datetime.timedelta(days=1)


async def update_menus(day):
    html = await _fetch.fetch_data_get_text(_menu_url)
    if html == -1:
        return -1
    html = bs4.BeautifulSoup(html, "html.parser", parse_only=bs4.SoupStrainer(id="menu-repas"))
    for menu in html.find_all("h3"):
        embed = discord.Embed()
        embed.type = "rich"
        embed.title = "Resto’ U de l’Illberg"
        embed.url = _menu_url
        embed.colour = random.randint(0, 16581375)
        embed.description = menu.text.strip()
        menu = menu.next_element.next_element.next_element
        menu = menu.find("h4", string=re.compile("Déjeuner")).next_element.next_element.next_element
        for group in menu.find_all('span'):
            name = group.text.strip()
            value = ""
            group = group.next_element.next_element
            try:
                for field in group.find_all('li'):
                    value += field.text.strip() + "\n"
            except AttributeError:
                pass
            if value == "":
                value = "¯\_(ツ)_/¯"
            embed.add_field(name=name, value=value, inline=False)
        _menus[embed.description] = embed
    try:
        return _menus[day]
    except KeyError:
        return -1


async def edit_menu(msg, day, client):
    menu_date = day.strftime("Menu du %A {0} %B %Y").format(day.day)
    try:
        await msg.edit(content="", embed=_menus[menu_date])
    except KeyError:
        menu = await update_menus(menu_date)
        if menu == -1:
            await msg.edit(content="Le {} n'a pas été trouvé sur le site :\n{}".format(menu_date.lower(), _menu_url),
                           embed=None)
        else:
            await msg.edit(content="", embed=menu)

    def checkreactionru(reaction, user):
        return user != client.user and msg.id == reaction.message.id \
               and (str(reaction.emoji == '⏪' or str(reaction.emoji == '⏩')))
    try:
        reaction, user = await client.wait_for('reaction_add', timeout=15.0, check=checkreactionru)
    except asyncio.TimeoutError:
        pass
        await msg.remove_reaction(emoji='⏪', member=msg.author)
        await msg.remove_reaction(emoji='⏩', member=msg.author)
    else:
        if reaction.emoji == '⏪':
            day = day - one_day
            if day.weekday() == 6:
                day = day - one_day - one_day
            await msg.remove_reaction(reaction.emoji, member=user)
            await edit_menu(msg, day, client)
        elif reaction.emoji == '⏩':
            day = day + one_day
            if day.weekday() == 5:
                day = day + one_day + one_day
            await msg.remove_reaction(reaction.emoji, member=user)
            await edit_menu(msg, day, client)


async def send_menu(ctx, day=datetime.date.today()):
    menu_date = day.strftime("Menu du %A {0} %B %Y").format(day.day)
    try:
        msg_sent = await ctx.send(embed=_menus[menu_date])
        await msg_sent.add_reaction(emoji='⏪')
        await msg_sent.add_reaction(emoji='⏩')
    except KeyError:
        menu = await update_menus(menu_date)
        if menu == -1:
            await ctx.send("Le {} n'a pas été trouvé sur le site :\n{}".format(menu_date.lower(), _menu_url))
            return 0
        else:
            msg_sent = await ctx.send(embed=menu)
            await msg_sent.add_reaction(emoji='⏪')
            await msg_sent.add_reaction(emoji='⏩')

    def checkreactionru(reaction, user):
        return user != ctx.bot.user and msg_sent.id == reaction.message.id \
               and (str(reaction.emoji == '⏪' or str(reaction.emoji == '⏩')))
    try:
        reaction, user = await ctx.bot.wait_for('reaction_add', timeout=15.0, check=checkreactionru)
    except asyncio.TimeoutError:
        await msg_sent.remove_reaction(emoji='⏪', member=msg_sent.author)
        await msg_sent.remove_reaction(emoji='⏩', member=msg_sent.author)
    else:
        if reaction.emoji == '⏪':
            day = day - one_day
            if day.weekday() == 6:
                day = day - one_day - one_day
            await msg_sent.remove_reaction(reaction.emoji, member=user)
            await edit_menu(msg_sent, day, ctx.bot)
        elif reaction.emoji == '⏩':
            day = day + one_day
            if day.weekday() == 5:
                day = day + one_day + one_day
            await msg_sent.remove_reaction(reaction.emoji, member=user)
            await edit_menu(msg_sent, day, ctx.bot)
