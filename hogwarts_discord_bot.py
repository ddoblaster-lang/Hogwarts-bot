import discord
from discord import app_commands
from discord.ext import commands
import json
from typing import Dict
import random
# ==============================
# HOGWARTS BOT CONFIG
# ==============================
import os
TOKEN = os.getenv("TOKEN")
GUILD_ID = 0  # Optional: put your server ID here to sync commands faster while testing

HOUSE_ROLES = {
    "gryffindor": 1494063578397933568,  # Replace with Gryffindor role ID
    "slytherin": 1494063673449123981,   # Replace with Slytherin role ID
    "ravenclaw": 1494063747453423830,   # Replace with Ravenclaw role ID
    "hufflepuff": 1494063836188246046,  # Replace with Hufflepuff role ID
}

DATA_FILE = "house_points.json"

HOUSE_EMOJIS = {
    "gryffindor": "🦁",
    "slytherin": "🐍",
    "ravenclaw": "🦅",
    "hufflepuff": "🦡",
}

HOUSE_DISPLAY = {
    "gryffindor": "Gryffindor",
    "slytherin": "Slytherin",
    "ravenclaw": "Ravenclaw",
    "hufflepuff": "Hufflepuff",
}
DATA_FILE = "house_points.json"

def load_points():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "gryffindor": 0,
        "slytherin": 0,
        "ravenclaw": 0,
        "hufflepuff": 0,
    }


def save_points(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree


async def remove_other_house_roles(member: discord.Member, keep_house: str):
    roles_to_remove = []
    for house, role_id in HOUSE_ROLES.items():
        if house != keep_house:
            role = member.guild.get_role(role_id)
            if role and role in member.roles:
                roles_to_remove.append(role)

    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Switching Hogwarts house")


async def assign_house(member: discord.Member, house: str):
    role_id = HOUSE_ROLES.get(house)
    if not role_id:
        raise ValueError(f"Missing role ID for house: {house}")

    role = member.guild.get_role(role_id)
    if role is None:
        raise ValueError(f"Could not find role for house: {house}")

    await remove_other_house_roles(member, house)
    if role not in member.roles:
        await member.add_roles(role, reason="Sorted into Hogwarts house")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} global commands")
    except Exception as e:
        print(f"Command sync failed: {e}")



@tree.command(name="myschool", description="See which house you are in")
async def myschool(interaction: discord.Interaction):
    member = interaction.user
    current_house = None

    for house, role_id in HOUSE_ROLES.items():
        role = member.guild.get_role(role_id)
        if role and role in member.roles:
            current_house = house
            break

    if current_house:
        await interaction.response.send_message(
            f"{HOUSE_EMOJIS[current_house]} You are in **{HOUSE_DISPLAY[current_house]}**.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            "You have not been sorted yet. Use **/sortme**.", ephemeral=True
        )


@tree.command(name="housecup", description="Show the current House Cup standings")
async def housecup(interaction: discord.Interaction):
    points = load_points()
    sorted_houses = sorted(points.items(), key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title="🏆 House Cup Standings", color=discord.Color.gold())
    for house, score in sorted_houses:
        embed.add_field(
            name=f"{HOUSE_EMOJIS[house]} {HOUSE_DISPLAY[house]}",
            value=f"{score} points",
            inline=False,
        )

    await interaction.response.send_message(embed=embed)


@tree.command(name="addpoints", description="Add points to a house (admin only)")
@app_commands.describe(house="House to reward", amount="How many points to add")
@app_commands.choices(
    house=[
        app_commands.Choice(name="Gryffindor", value="gryffindor"),
        app_commands.Choice(name="Slytherin", value="slytherin"),
        app_commands.Choice(name="Ravenclaw", value="ravenclaw"),
        app_commands.Choice(name="Hufflepuff", value="hufflepuff"),
    ]
)
@app_commands.checks.has_permissions(manage_guild=True)
async def addpoints(interaction: discord.Interaction, house: app_commands.Choice[str], amount: int):
    points = load_points()

    points[house.value] += amount
    save_points(points)

    await interaction.response.send_message(
        f"Added **{amount}** points to {HOUSE_EMOJIS[house.value]} **{HOUSE_DISPLAY[house.value]}**.",
        ephemeral=True
    )

@tree.command(name="removepoints", description="Remove points from a house (admin only)")
@app_commands.describe(house="House to penalize", amount="How many points to remove")
@app_commands.choices(
    house=[
        app_commands.Choice(name="Gryffindor", value="gryffindor"),
        app_commands.Choice(name="Slytherin", value="slytherin"),
        app_commands.Choice(name="Ravenclaw", value="ravenclaw"),
        app_commands.Choice(name="Hufflepuff", value="hufflepuff"),
    ]
)
@app_commands.checks.has_permissions(manage_guild=True)
async def removepoints(interaction: discord.Interaction, house: app_commands.Choice[str], amount: int):
    points = load_points()
    points[house.value] -= amount
    save_points(points)

    await interaction.response.send_message(
        f"Removed **{amount}** points from {HOUSE_EMOJIS[house.value]} **{HOUSE_DISPLAY[house.value]}**."
    )


@addpoints.error
@removepoints.error
async def admin_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        if interaction.response.is_done():
            await interaction.followup.send("You need **Manage Server** to use that command.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "You need **Manage Server** to use that command.", ephemeral=True
            )
    else:
        if interaction.response.is_done():
            await interaction.followup.send(f"Error: {error}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Error: {error}", ephemeral=True)


@tree.command(name="resetcup", description="Reset House Cup scores to 0 (admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def resetcup(interaction: discord.Interaction):
    points = load_points()

    for house in points:
        points[house] = 0

    save_points(points)

    await interaction.response.send_message(
        "🏆 House Cup scores have been reset.",
        ephemeral=True
    )

@tree.command(name="sortme", description="Get randomly sorted into a Hogwarts house")
async def sortme(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        house = random.choice(list(HOUSE_ROLES.keys()))

        await assign_house(interaction.user, house)

        emoji = HOUSE_EMOJIS[house]
        display = HOUSE_DISPLAY[house]

        await interaction.followup.send(
            f"🎩 *Hmm... difficult... very difficult...*\n\n"
            f"🎩 *But I know exactly where to put you...*\n\n"
            f"{emoji} **{display.upper()}!**\n\n"
            f"✨ Wear your house with pride.",
            ephemeral=True
        )


    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)
if __name__ == "__main__":
    bot.run(TOKEN)
