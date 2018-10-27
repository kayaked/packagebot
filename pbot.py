import discord, os, asyncio, json, requests
from discord.ext.commands import Bot

# Please excuse the code, it's pretty bad right now

# Imports configuration
with open('guild_config.json', 'r') as fp:
    config = json.load(fp)

bot = Bot(command_prefix=config['about']['prefix'])


print("Package/pbot RC1")
first_setup = True
print("A new type of discord bot.")
print("WARNING: The following will create a new custom Package guild. It may take some time, and I (yak) cannot guarantee that there will be no issues during this time.")
proceed = input("Are you sure you wish to proceed? (y/n): ")
if proceed.upper() == "N":
    print("Well, I'll always be here if you want. Goodbye!")
    exit()
if config['about']['token']:
    token = config['about']['token']
else:
    token = input("Please input/paste your Discord Bot Token here: ")

# Leaves a guild if not created by Package
@bot.event
async def on_guild_join(guild):
    if not guild.owner.id==bot.user.id:
        await guild.leave()


# Auto gives owner admin on join (formality)
@bot.event
async def on_member_join(member):
    if member.id == bot.appinfo.owner.id and member.guild.owner.id == bot.user.id:
        print("Owner ready state detected")
        await member.guild.edit(owner=bot.appinfo.owner)
        await member.guild.leave()
        print("Thank you for using Package to create your community!")
        await bot.logout()
        exit()

@bot.event
async def on_ready():
    if not hasattr(bot, 'appinfo'):
        bot.appinfo = await bot.application_info()
    print("Logged in with bot owner {}".format(bot.appinfo.owner))
    if bot.guilds.__len__() > 0:
        if bot.appinfo.owner.id in [user.id for user in bot.guilds[0].members] and bot.guilds[0].owner.id == bot.user.id:
            print("Owner ready state detected")
            await bot.guilds[0].edit(owner=bot.appinfo.owner)
            await bot.guilds[0].leave()
            print("Thank you for using Package to create your community!")
            await bot.logout()
            exit()
        else:
            print("WARNING: Bot has already made a guild (server), but you have not claimed ownership.")
            g = input("Continue and DELETE server or get invite? (d/i)")
            if g=="d":
                pass
            else:
                inv = await bot.guilds[0].text_channels[0].create_invite()
                print("Current invite: {}".format(inv))
                print("Join guild now while package is online to claim ownership!")
                return
    for server in bot.guilds: await server.delete()
    if config['about']['name']==None:
        name = input("Name of Guild (Server): ")
        if name == "":
            name = "An awesome Package guild"
    else:
        name = config['about']['name']
    create_kw = {}
    if config['about']['icon_url']:
        create_kw['icon'] = requests.get(config['about']['icon_url']).content
    ng = await bot.create_guild(name, region=getattr(discord.VoiceRegion, config['about']['region']), **create_kw)
    print("Loading guild...")

    # Sleeps to cooldown on guild creation
    await asyncio.sleep(5)

    # Deletes default channels (just to prevent issue)
    for channel in bot.get_all_channels(): await channel.delete()

    d_r = "Package-created Role"
    d_c = "Package-created Channel"
    d_e = "Package-created Event"

    # Roles (This sleeps for 0.5 sec to cooldown)
    rnames = {}
    cats = {}
    for role in config['roles']:
        if role['colour'].startswith("#"):
            colour = discord.Colour(eval("0x" + role['colour'][1:]))
        else:
            colour = getattr(discord.Colour, role['color'])()
        rnames[role['name']] = await ng.create_role(name=role['name'], permissions=discord.Permissions(permissions=role['permissions']), hoist=role['hoist'], color=colour, reason=d_r)
        await asyncio.sleep(0.5)

    # Creates all channels from the JSON config
    invite_c = None
    for category in config['channel_categories']:

        overwrites = {}
        for key, value in category['permissions'].items():
            if key=="@everyone":
                overwrites[ng.default_role] = discord.PermissionOverwrite(**value)
            else:
                overwrites[discord.utils.get(bot.guilds[0].roles, name=key)] = discord.PermissionOverwrite(**value)
        
        print(overwrites)

        cats[category['name']] = await ng.create_category_channel(category['name'], overwrites=overwrites, reason=d_c)
        for channel in category['channels']:
            ch_overwrites = {}

            if channel['permissions']:
                for key, value in channel['permissions'].items():
                    if key=="@everyone":
                        ch_overwrites[ng.default_role] = discord.PermissionOverwrite(**value)
                    else:
                        ch_overwrites[discord.utils.get(bot.guilds[0].roles, name=key)] = discord.PermissionOverwrite(**value)
            
            if channel['type']=="text":
                newchannelinstance = await ng.create_text_channel(channel['name'], category=cats[category['name']], overwrites=ch_overwrites, reason=d_c)

                if "description" in channel:
                    await newchannelinstance.edit(topic=channel['description'], reason=d_c)
                
                if "auto_message" in channel:
                    await newchannelinstance.send(channel['auto_message'])

                if invite_c==None:
                    invite_c = await newchannelinstance.create_invite(reason=d_e) # Creates invite to first channel
            elif channel['type']=="voice":
                await ng.create_voice_channel(channel['name'], category=cats[category['name']], overwrites=ch_overwrites, reason=d_c)
    print(invite_c)

bot.run(token)