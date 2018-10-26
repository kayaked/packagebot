import discord, os, asyncio, json, requests
from discord.ext.commands import Bot

# Please excuse the code, it's pretty bad right now

# Imports configuration
with open('guild_config.json', 'r') as fp:
    config = json.load(fp)

bot = Bot(command_prefix=config['about']['prefix'])

if os.path.isfile('.package_no_barge'):
    print("Welcome back!")
    first_setup = False
else:
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
    with open('.package_no_barge', 'w+') as fp:
        fp.write(token)
    
# Give a user the role named Administrator (doesnt work with role integers) (owner only)
@bot.command(name="owner_ao")
async def owner_administrator_override(ctx, user:discord.Member):
    if ctx.message.author.id==bot.appinfo.owner.id:
        await user.add_roles(discord.utils.get(ctx.guild.roles, name="Administrator"))

# Give a user the role named Moderator (doesnt work with role integers) (owner only)
@bot.command(name="owner_mo")
async def owner_moderator_override(ctx, user:discord.Member):
    if ctx.message.author.id==bot.appinfo.owner.id:
        await user.add_roles(discord.utils.get(ctx.guild.roles, name="Moderator"))

# Deletes .package_no_barge save file (does NOT steal your token) (owner only)
@bot.command(name="owner_pnbo")
async def owner_package_no_barge_override(ctx):
    if ctx.message.author.id==bot.appinfo.owner.id:
        os.remove('.package_no_barge')

# Auto gives owner admin on join (formality)
@bot.event
async def on_member_join(member):
    if member.id==bot.appinfo.owner.id:
        await member.add_roles(discord.utils.get(member.guild.roles, name="Administrator"))
    if bot.appinfo.owner.id in [user.id for user in member.guild.members] and member.guild.owner.id == bot.user.id:
        print("Owner ready state detected!")
        await member.guild.edit(owner=bot.appinfo.owner)

@bot.event
async def on_ready():
    if not hasattr(bot, 'appinfo'):
        bot.appinfo = await bot.application_info()
    print("Logged in with bot owner {}".format(bot.appinfo.owner))
    if first_setup==True:
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
        for role in config['roles']:
            rnames[role['name']] = await ng.create_role(name=role['name'], permissions=discord.Permissions(permissions=role['permissions']), hoist=role['hoist'], color=getattr(discord.Colour, role['color'])(), reason=d_r)
            await asyncio.sleep(0.5)
            # Establishes variable roles without exec() fucking my stuff up (Might switch this to a dict or remove it entirely)
            if rnames[role['name']].permissions.value == config['about']['role_definitions']['pkg_staffs']:
                mod = rnames[role['name']]
            if rnames[role['name']].permissions.value == config['about']['role_definitions']['pkg_admin']:
                admin = rnames[role['name']]
            if rnames[role['name']].permissions.value == config['about']['role_definitions']['pkg_trusted']:
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
                if channel['type']=="text":
                    newchannelinstance = await ng.create_text_channel(channel['name'], category=cats[category['name']])
                    if invite_c==None:
                        invite_c = await newchannelinstance.create_invite() # Creates invite to first channel
                elif channel['type']=="voice":
                    await ng.create_voice_channel(channel['name'], category=cats[category['name']])
        myself = bot.get_all_members()
        if admin: await discord.utils.get(myself).add_roles(admin)
        print(invite_c)
    else:
        if bot.appinfo.owner.id in [user.id for user in bot.guilds[0].members] and bot.guilds[0].owner.id == bot.user.id:
            print("Owner ready state detected!")
            await bot.guilds[0].edit(owner=bot.appinfo.owner)
        print("I'm ready!")
        inv = await bot.guilds[0].invites()
        print("Current Server Invite: " + str(inv[0]))

# Deletes all servers (owner only)
@bot.command(name="owner_dso")
async def owner_delete_server_override(ctx):
    if ctx.message.author.id==bot.appinfo.owner.id:
        for server in bot.guilds: await server.delete() 

final_token = ""
with open('.package_no_barge', 'r') as fp:
    final_token = fp.read()

bot.run(final_token)