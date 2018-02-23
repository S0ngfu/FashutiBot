import discord
from discord.ext import commands

import config as _config
import ru as _ru
import edt as _edt

fashuti_bot = commands.Bot(command_prefix=',')


@fashuti_bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


@fashuti_bot.event
async def on_ready():
    print('Logged in as')
    print(fashuti_bot.user.name)
    print(fashuti_bot.user.id)
    print('------')


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
                                                                    name="Chackal jouer à {0.name}".format(after.game)))
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


@fashuti_bot.command()
async def ru(ctx):
    await _ru.send_menu(ctx)


@fashuti_bot.command()
async def edt(ctx, cursus: str = "m1miage"):
    await _edt.send_edt(ctx, cursus)


fashuti_bot.run(_config.discord_token)
