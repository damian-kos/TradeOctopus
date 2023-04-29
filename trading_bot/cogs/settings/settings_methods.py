from embed.embed_message import embed_settings_message
from embed.embed_confirmation import Confirmation
from webhook.create_webhook import create_webhook_


async def channel_settings_return_messages(channel, db, ctx, test_view=None):
    channels_info = {
        "listing_channel": [
            "Listing Channel",
            "new listings are sent.",
            "Trading Listing",
        ],
        "search_channel": [
            "Search Channel",
            "search results are sent.",
            "Trading Search",
        ],
        "sell_channel": [
            "Sell Channel",
            "you can post a new item. Once posted it will be sent on a 'listing_channel'.",
            "Trading Selling",
        ],
        "logging": [
            "Logging Channel",
            "server log messages are sent.",
            "Trading Logging",
        ],
    }
    guild = db.guild_in_database(guild_id=ctx.guild.id)
    title = f"{channels_info[channel][0]} - Settings"
    description = f"Changes the channel where {channels_info[channel][1]}"

    if guild is not None:
        try:
            current_value = (
                f"{ctx.guild.get_channel(guild[channel])}: {guild[channel]}"
            )
        except KeyError:
            current_value = "Not set yet."

    if test_view is not None:
        last_item_in_message = ctx.message.content.split(" ")[-1]
        channel_id = channel_to_set_id(last_item_in_message, ctx=ctx)
        test_view.response = await ctx.send(
            f"Are you sure you want https://discord.com/channels/{ctx.guild.id}/{channel_id} as the new {channel}?",
            view=test_view,
            delete_after=20,
        )
        await test_view.wait()
        if test_view.value:
            await create_webhook_(
                ctx=ctx,
                channel_id=channel_id,
                new_webhook_name=channels_info[channel][2],
            )
            db.set_channel(
                guild_id=ctx.guild.id,
                channel_id=channel_id,
                channel_type=channel,
            )
            await ctx.send(
                f"✅ https://discord.com/channels/{ctx.guild.id}/{channel_id} will now be used as the {channel}."
            )
        else:
            print("No")
    else:
        embed = embed_settings_message(
            msg_title=title,
            msg_desc=description,
            current_value_field=current_value,
            edit_field=f"`/settings {channel} [channel]`",
            accepted_value=f"A channel's name or ID.",
            rgb_color=(255, 255, 0),  # yellow,
        )
        await ctx.send(embed=embed)


def channel_to_set_id(last_item_of_message, ctx):
    channel_to_set = last_item_of_message
    guild_channels_id = tuple(channel.id for channel in ctx.guild.channels)
    if channel_to_set.isdigit():
        if int(channel_to_set) in guild_channels_id:
            chosen_channel = int(channel_to_set)
    else:
        for channel in ctx.guild.channels:
            if str(channel) == channel_to_set:
                chosen_channel = channel.id
                break
    return chosen_channel


async def set_channel(ctx, db):
    modified_channel = ctx.message.content.split(" ")[1]
    if len(ctx.message.content.split(" ")) == 3:
        await channel_settings_return_messages(
            channel=modified_channel,
            db=db,
            ctx=ctx,
            test_view=Confirmation(),
        )
        return
    await channel_settings_return_messages(
        channel=modified_channel,
        db=db,
        ctx=ctx,
    )


async def item_properties_settings_embed_message(
    db, ctx, title_suffix, rgb_color
):
    item_properties_info = {
        "item_properties": [
            "Item Properties",
            (
                "Changes the way your items are stored,"
                "be careful once you setup it you shouldn't change it later.\n "
                "Unless you delete all your items from database.\n"
                "Items will always be having `price` property so you don't need to add this."
            ),
        ],
    }
    title = f'{item_properties_info["item_properties"][0]} - {title_suffix}'
    description = item_properties_info["item_properties"][1]
    guild = db.guild_in_database(
        guild_id=ctx.guild.id
    )  # get refreshed collection within same command
    current_value = guild["item_properties"]
    # print(guild)

    print(type(current_value))
    print(len(current_value))
    print(current_value == [])
    if current_value == []:
        current_value = "Not set yet."
    embed = embed_settings_message(
        msg_title=title,
        msg_desc=description,
        current_value_field=current_value,
        edit_field=f"`/settings item_properties [property1] [property2]",
        accepted_value=(
            f"Single word property like `title` or `release_date`.\n"
            "If you set it like:\n"
            "`/settings item_properties make model part color item_description`\n"
            "It will automatically add `price` property at the end."
        ),
        rgb_color=rgb_color,  # yellow
    )
    await ctx.send(embed=embed)


async def define_item_properties(ctx, db):
    guild = db.guild_in_database(guild_id=ctx.guild.id)
    item_properties = ctx.message.content.split(" ")[2:]
    if item_properties != []:
        item_properties = tuple(column.strip() for column in item_properties)
        db.define_item_properties(
            guild_id=ctx.guild.id,
            item_properties_tuple=item_properties,
        )
        await item_properties_settings_embed_message(
            db=db,
            ctx=ctx,
            title_suffix="Modified",
            rgb_color=(102, 255, 51),
        )
    else:
        await item_properties_settings_embed_message(
            db=db,
            ctx=ctx,
            title_suffix="Settings",
            rgb_color=(255, 255, 0),
        )


async def role_can_embed_message(function, db, ctx, title_suffix, rgb_color):
    function_info = {
        "can_remove": ["Can Remove", "remove listing from database."],
        "can_search": ["Can Search", "search through listings in database."],
        "can_sell": [
            "Can Sell",
            "add new listings to database.",
        ],
    }
    guild = db.guild_in_database(guild_id=ctx.guild.id)
    title = function_info[function][0]
    description = f"Changes the role which can{function_info[function][1]}"
    if guild is not None:
        try:
            current_value = f"{guild[function]}"
        except KeyError:
            current_value = "Not set yet."
    embed = embed_settings_message(
        msg_title=f"{title} - {title_suffix}",
        msg_desc=description,
        current_value_field=current_value,
        edit_field=f"`/settings {function} [role]`",
        accepted_value=f"A role's name or `all`.",
        rgb_color=rgb_color,
    )
    await ctx.send(embed=embed)


async def role_can(ctx, db):
    message = ctx.message.content.split(" ")
    function = message[1]
    guild = db.guild_in_database(guild_id=ctx.guild.id)
    if len(message) == 3:
        role_assigned = message[-1]
        db.allow_role_to(
            guild_id=ctx.guild.id,
            function=function,
            role=role_assigned,
        )
        await role_can_embed_message(
            function=function,
            db=db,
            ctx=ctx,
            title_suffix="Modified",
            rgb_color=(255, 255, 0),  # yellow
        )
    else:
        await role_can_embed_message(
            function=function,
            db=db,
            ctx=ctx,
            title_suffix="Settings",
            rgb_color=(102, 255, 51),
        )
