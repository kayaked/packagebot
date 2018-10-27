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
    if member.id==bot.appinfo.owner.id:
        for role in member.guild.roles:
            if role.permissions.value in config['about']['role_definitions']['pkg_admin']:
                await member.add_roles(role)
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
        if bot.appinfo.owner.id in [user.id for user in bot.guilds[0].members]:
            for role in bot.guilds[0].roles:
                if role.permissions.value in config['about']['role_definitions']['pkg_admin']:
                    await discord.utils.get(bot.get_all_members(), id=bot.appinfo.owner.id).add_roles(role)
        if bot.appinfo.owner.id in [user.id for user in bot.guilds[0].members] and bot.guilds[0].owner.id == bot.user.id:
            print("Owner ready state detected")
            await bot.guilds[0].edit(owner=bot.appinfo.owner)
            await bot.guilds[0].leave()
            print("Thank you for using Package to create your community!")
            await bot.logout()
            exit()
        else:
            print("WARNING: Bot has already made a guild (server), but you have not claimed ownership.")
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

    d_r = "Package-created Role" # soft-code message

    # Roles (This sleeps for 0.5 sec to cooldown)
    rnames = {}
    cats = {}
    admin = None
    mod = None
    trusted = None
    for role in config['roles']:
        rnames[role['name']] = await ng.create_role(name=role['name'], permissions=discord.Permissions(permissions=role['permissions']), hoist=role['hoist'], color=getattr(discord.Colour, role['color'])(), reason=d_r)
        await asyncio.sleep(0.5)
        # Establishes variable roles without exec() fucking my stuff up (Might switch this to a dict or remove it entirely)
        if rnames[role['name']].permissions.value in config['about']['role_definitions']['pkg_staffs']:
            mod = rnames[role['name']]
        if rnames[role['name']].permissions.value in config['about']['role_definitions']['pkg_admin']:
            admin = rnames[role['name']]
        if rnames[role['name']].permissions.value in config['about']['role_definitions']['pkg_trusted']:
            trusted = rnames[role['name']]


    # Staff channel permissions (might merge with code above)
    # pkg_staffs = Moderators and Admins
    # pkg_admin = Admins
    # pkg_trusted = Trusted and Admins
    # pkg_trusted_staff = Trusted Moderators and Admins
    # pkg_staff_announce = Send messages disabled for non-staff
    # pkg_admin_announce = Send messages disabled for non-admin
    pkg_staffs = {
        ng.default_role:discord.PermissionOverwrite(read_messages=False),
        mod:discord.PermissionOverwrite(read_messages=True)
    }
    pkg_admin = {
        ng.default_role:discord.PermissionOverwrite(read_messages=False),
        admin:discord.PermissionOverwrite(read_messages=True)
    }
    pkg_trusted = {
        ng.default_role:discord.PermissionOverwrite(read_messages=False),
        trusted:discord.PermissionOverwrite(read_messages=True)
    }
    pkg_trusted_staff = {
        ng.default_role:discord.PermissionOverwrite(read_messages=False),
        trusted:discord.PermissionOverwrite(read_messages=True),
        mod:discord.PermissionOverwrite(read_messages=True)
    }
    pkg_staff_announce = {
        ng.default_role:discord.PermissionOverwrite(send_messages=False),
        mod:discord.PermissionOverwrite(send_messages=True)
    }
    pkg_admin_announce = {
        ng.default_role:discord.PermissionOverwrite(send_messages=False)
    }
    
    pkg_everyone = {
    }

    pkg_everyone; pkg_staffs; pkg_admin; pkg_trusted; pkg_trusted_staff; pkg_staff_announce; pkg_admin_announce
    # Calls all pkg perms so they aren't green in VSCode

    # Creates all channels from the JSON config
    invite_c = None
    for category in config['channel_categories']:
        cats[category['name']] = await ng.create_category_channel(category['name'], overwrites=eval(category['permissions']))
        for channel in category['channels']:
            channel_kw = {}
            if channel['permissions']: channel_kw['overwrites'] = eval(channel['permissions'])
            if channel['type']=="text":
                newchannelinstance = await ng.create_text_channel(channel['name'], category=cats[category['name']], **channel_kw)

                if "description" in channel:
                    await newchannelinstance.edit(topic=channel['description'])
                
                if "auto_message" in channel:
                    await newchannelinstance.send(channel['auto_message'])

                if invite_c==None:
                    invite_c = await newchannelinstance.create_invite() # Creates invite to first channel
            elif channel['type']=="voice":
                await ng.create_voice_channel(channel['name'], category=cats[category['name']], **channel_kw)
    myself = bot.get_all_members()
    if admin: await discord.utils.get(myself).add_roles(admin)
    print(invite_c)
        




bot.run(token)