import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from datetime import datetime
import io
import json

intents = discord.Intents.default()

VOUCH_DB_FILE = "vouch_data.json"
TICKETS_DB_FILE = "tickets_db.json"

def load_vouch_data():
    try:
        if os.path.exists(VOUCH_DB_FILE):
            with open(VOUCH_DB_FILE, 'r') as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        return {}
    except Exception as e:
        print(f"Error loading vouch data: {e}")
        return {}

def save_vouch_data():
    try:
        data_to_save = {str(k): v for k, v in vouch_data.items()}
        with open(VOUCH_DB_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=2)
    except Exception as e:
        print(f"Error saving vouch data: {e}")

def load_tickets_db():
    try:
        if os.path.exists(TICKETS_DB_FILE):
            with open(TICKETS_DB_FILE, 'r') as f:
                data = json.load(f)
            mm = {int(k): v for k, v in data.get("mm", {}).items()}
            support = {int(k): v for k, v in data.get("support", {}).items()}
            index = {int(k): v for k, v in data.get("index", {}).items()}
            # Convert created_at strings back to datetime
            for d in [mm, support, index]:
                for t in d.values():
                    if isinstance(t.get("created_at"), str):
                        try:
                            t["created_at"] = datetime.fromisoformat(t["created_at"])
                        except:
                            t["created_at"] = datetime.utcnow()
            return mm, support, index
        return {}, {}, {}
    except Exception as e:
        print(f"Error loading tickets DB: {e}")
        return {}, {}, {}

def save_tickets_db():
    try:
        def serialize(d):
            out = {}
            for k, v in d.items():
                entry = dict(v)
                if isinstance(entry.get("created_at"), datetime):
                    entry["created_at"] = entry["created_at"].isoformat()
                # Remove non-serializable fields
                entry.pop("messages", None)
                out[str(k)] = entry
            return out
        data = {
            "mm": serialize(active_tickets),
            "support": serialize(active_support_tickets),
            "index": serialize(active_index_tickets),
        }
        with open(TICKETS_DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving tickets DB: {e}")

intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

CONFIG = {
    "MIDDLEMAN_ROLE_ID": 1471834637373407387,
    "LEAD_COORD_ROLE_ID": 1471834602980249644,
    "TRUSTED_TRADER_ROLE_ID": 1471834534113710254,
    "COMPLETE_LOG_CHANNEL_ID": 1475040955240288368,
    "INDEX_CONFIRM_LOG_CHANNEL_ID": 1475701915164737640,
    "SMALL_TRADE_CLAIM_ROLE_ID": 1471834637373407387,
    "BIG_TRADE_CLAIM_ROLE_ID": 1471834602980249644,
    "MASSIVE_TRADE_CLAIM_ROLE_ID": 1471834534113710254,
    "SMALL_TRADE_PING_ROLE_ID": 1471834637373407387,
    "BIG_TRADE_PING_ROLE_ID": 1471834602980249644,
    "MASSIVE_TRADE_PING_ROLE_ID": 1471834534113710254,
    "TICKET_CATEGORY_ID": 1471874614648115336,
    "BIG_TRADE_CATEGORY_ID": 1473641831014076540,
    "MASSIVE_TRADE_CATEGORY_ID": 1473642698756980799,
    "LOG_CHANNEL_ID": 1471834958107639829,
    "STAFF_CHAT_ID": 1471834830995198158,
    "VERIFIED_ROLE_ID": 1471834670990757908,
    "TRANSCRIPT_CHANNEL_ID": 1473639492467560612,
    "BAN_PERMS_ROLE_ID": 1472343225883955291,
    "WELCOME_CHANNEL_ID": 1471834830995198158,
    "SUPPORT_CATEGORY_ID": 1471834729249767567,
    "SUPPORT_PING_ROLE_ID": 1471834568955924601,
    "SUPPORT_LOG_CHANNEL_ID": 1473617007906914378,
    "INDEX_CATEGORY_ID": 1475697295424225350,
    "INDEX_PING_ROLE_ID": 1471834603152212091,
    "INDEX_LOG_CHANNEL_ID": 1475697785100697773,
    "SUPREME_ROLE_ID": 1471834568997998603,
    "SERVER_ICON": "https://cdn.discordapp.com/icons/986944910391394325/a_0b9f9d765647fe163d28210a0a70fa2d.gif?size=4096",
    "SERVER_BANNER": "https://media.discordapp.net/attachments/1473040236379639868/1473136778067312813/ricks_middleman_fixed_fast_snow.gif?ex=69951d09&is=6993cb89&hm=67dd725ea3a3154074a7aca84aec7e0190100afd0092abb24fd51266e6f524ec&=&width=993&height=559",
}

active_tickets = {}
active_support_tickets = {}
blacklist = set()
verified_users = set()
afk_users = {}

# Load persisted ticket data
_mm, _support, _index = load_tickets_db()
active_tickets.update(_mm)
active_support_tickets.update(_support)
active_index_tickets = _index

SERVER_RULES = [
    {"number": 1, "title": "Be Respectful", "description": "Treat everyone with kindness."},
    {"number": 2, "title": "No NSFW or Inappropriate Content", "description": "Keep things clean."},
    {"number": 3, "title": "Use Common Sense", "description": "Don't look for loopholes."},
    {"number": 4, "title": "No Spam or Self-Promo", "description": "No advertising or spam."},
    {"number": 5, "title": "Respect Privacy", "description": "Don't leak private info."},
    {"number": 6, "title": "Follow Staff Instructions", "description": "Respect all staff."},
    {"number": 7, "title": "No Unapproved Bots or Exploits", "description": "Don't use or abuse unauthorized bots."},
    {"number": 8, "title": "Stay in the Right Channels", "description": "Use channels appropriately."},
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def is_staff(member: discord.Member) -> bool:
    """Check if member has any staff role or is admin."""
    if member.guild_permissions.administrator:
        return True
    staff_ids = [CONFIG["MIDDLEMAN_ROLE_ID"], CONFIG["LEAD_COORD_ROLE_ID"],
                 CONFIG["TRUSTED_TRADER_ROLE_ID"], CONFIG["SUPPORT_PING_ROLE_ID"]]
    return any(r.id in staff_ids for r in member.roles)

async def lock_staff_roles(channel, guild):
    for key in ("MIDDLEMAN_ROLE_ID", "LEAD_COORD_ROLE_ID", "TRUSTED_TRADER_ROLE_ID"):
        role = guild.get_role(CONFIG[key])
        if role:
            await channel.set_permissions(role, view_channel=True, send_messages=False)

async def unlock_staff_roles(channel, guild):
    for key in ("MIDDLEMAN_ROLE_ID", "LEAD_COORD_ROLE_ID", "TRUSTED_TRADER_ROLE_ID"):
        role = guild.get_role(CONFIG[key])
        if role:
            await channel.set_permissions(role, view_channel=True, send_messages=True)

# ─────────────────────────────────────────────────────────────────────────────
# TRANSCRIPT
# ─────────────────────────────────────────────────────────────────────────────

async def save_transcript_and_send(channel: discord.TextChannel, closed_by: discord.Member):
    ticket = active_tickets.get(channel.id, {})
    guild = channel.guild
    owner_id = ticket.get("owner")
    claimer_id = ticket.get("claimed_by")
    owner = guild.get_member(owner_id) if owner_id else None
    claimer = guild.get_member(claimer_id) if claimer_id else None
    messages = []
    async for msg in channel.history(limit=None, oldest_first=True):
        messages.append(msg)
    value_display = str(ticket.get('value_raw', ticket.get('value', 'N/A')))
    lines = [
        f"Transcript for #{channel.name}",
        f"Ticket Creator : {owner.name if owner else owner_id}",
        f"Claimed By     : {claimer.name if claimer else 'Unclaimed'}",
        f"Closed By      : {closed_by.name}",
        f"Closed At      : {datetime.utcnow().strftime('%A, %B %d, %Y %I:%M %p')} UTC",
        f"Trade Type     : {ticket.get('type', 'N/A')}",
        f"Trade Value    : {value_display}",
        f"Total Messages : {len(messages)}", "", "─"*60, "",
    ]
    for msg in messages:
        ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = msg.content or ""
        if msg.attachments:
            content += " [Attachments: " + " | ".join(a.url for a in msg.attachments) + "]"
        if msg.embeds:
            content += f" [+{len(msg.embeds)} embed(s)]"
        lines.append(f"[{ts}] {msg.author.name} ({msg.author.id}): {content}")
    lines += ["", "─"*60, "Powered by Rick's Middleman"]
    transcript_text = "\n".join(lines)
    file_obj = discord.File(fp=io.BytesIO(transcript_text.encode("utf-8")), filename=f"transcript-{channel.id}.txt")
    embed = discord.Embed(title=f"📄 Transcript for #{channel.name}", color=0xFF6B00, timestamp=datetime.utcnow())
    embed.add_field(name="Ticket Creator", value=owner.mention if owner else f"`{owner_id}`", inline=True)
    embed.add_field(name="Claimed By", value=claimer.mention if claimer else "Unclaimed", inline=True)
    embed.add_field(name="Closed By", value=closed_by.mention, inline=True)
    embed.add_field(name="Closed At", value=f"<t:{int(datetime.utcnow().timestamp())}:F>", inline=True)
    embed.add_field(name="Trade Type", value=ticket.get("type", "N/A"), inline=True)
    embed.add_field(name="Trade Value", value=value_display, inline=True)
    embed.add_field(name="Total Messages", value=str(len(messages)), inline=True)
    embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
    embed.set_footer(text="Powered by Rick's Middleman", icon_url=CONFIG["SERVER_ICON"])
    tc = bot.get_channel(CONFIG["TRANSCRIPT_CHANNEL_ID"])
    if tc:
        await tc.send(embed=embed, file=file_obj)
    return transcript_text

# ─────────────────────────────────────────────────────────────────────────────
# VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────

class VerificationView(discord.ui.View):
    def __init__(self, user, recruiter=None):
        super().__init__(timeout=60)
        self.user = user
        self.recruiter = recruiter
        self.value = None

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="verify_accept")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ This verification is not for you!", ephemeral=True)
            return
        self.value = True
        self.stop()
        role = interaction.guild.get_role(CONFIG["VERIFIED_ROLE_ID"])
        if role:
            await self.user.add_roles(role)
        verified_users.add(self.user.id)
        e = discord.Embed(title="Verification Successful", description=f"Verification accepted.\n{datetime.utcnow().strftime('%d/%m/%Y %H:%M')}", color=0xFF6B00)
        e.set_footer(text="Powered by Rick's Middleman")
        await interaction.response.edit_message(embed=e, view=None)
        lc = interaction.client.get_channel(CONFIG["LOG_CHANNEL_ID"])
        if lc:
            le = discord.Embed(title="✅ User Verified", description=f"{self.user.mention} has been verified", color=0xFF6B00, timestamp=datetime.utcnow())
            le.set_thumbnail(url=self.user.display_avatar.url)
            if self.recruiter:
                le.add_field(name="Recruited by", value=self.recruiter.mention, inline=True)
            le.set_footer(text=f"User ID: {self.user.id}", icon_url=CONFIG["SERVER_ICON"])
            await lc.send(embed=le)
        wc = interaction.client.get_channel(CONFIG["WELCOME_CHANNEL_ID"])
        if wc:
            we = discord.Embed(description=f"**Hi {self.user.mention} Welcome to Brokeboi's Hitting Services**\n\n• Make sure to follow Discord's TOS\n• Please ask a middleman if you have any questions about hitting\n• Check <#1471834841925288060> if you are still confused.", color=0xFF6B00)
            we.set_thumbnail(url=self.user.display_avatar.url)
            we.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
            await wc.send(embed=we)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, custom_id="verify_decline")
    async def decline_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ This verification is not for you!", ephemeral=True)
            return
        self.value = False
        self.stop()
        e = discord.Embed(title="Verification Declined", description="You have declined the verification. You can try again later.", color=0xFF6B00)
        e.set_footer(text="Powered by Rick's Middleman")
        await interaction.response.edit_message(embed=e, view=None)

    async def on_timeout(self):
        e = discord.Embed(title="Verification Timeout", description="You didn't respond in time. Please try again.", color=0xFF6B00)
        e.set_footer(text="Powered by Rick's Middleman")
        if self.message:
            try:
                await self.message.edit(embed=e, view=None)
            except:
                pass

# ─────────────────────────────────────────────────────────────────────────────
# TRADE TICKET SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

class TradeTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Small Trade", description="0-500M Combined Earnings", emoji="💰"),
            discord.SelectOption(label="Big Trade", description="500M-2B Combined Earnings", emoji="💎"),
            discord.SelectOption(label="Massive Trade", description="5B+ Combined Earnings", emoji="👑"),
        ]
        super().__init__(placeholder="Select trade size...", options=options, min_values=1, max_values=1, custom_id="trade_select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TradeInfoModal(self.values[0]))

class TradeTypeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TradeTypeSelect())

class TradeInfoModal(discord.ui.Modal, title="Rick's MM Request"):
    def __init__(self, trade_type):
        super().__init__()
        self.trade_type = trade_type

    trading_with = discord.ui.TextInput(label="Who are you trading with?", placeholder="Enter their username...", required=True, style=discord.TextStyle.short)
    trade_details = discord.ui.TextInput(label="What is the trade?", placeholder="Describe the trade details...", required=True, style=discord.TextStyle.paragraph)
    trade_value = discord.ui.TextInput(label="Approximate Trade Value", placeholder="e.g., 500M or 1B", required=True, style=discord.TextStyle.short)
    can_join_links = discord.ui.TextInput(label="Can you and your partner join links?", placeholder="Yes/No", required=True, style=discord.TextStyle.short)
    roblox_users = discord.ui.TextInput(label="If not, send both Roblox usernames", placeholder="User1, User2 (leave empty if you can join links)", required=False, style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id in blacklist:
            await interaction.response.send_message("❌ You are currently blacklisted from using Rick's MM services.", ephemeral=True)
            return
        for t in active_tickets.values():
            if t["owner"] == interaction.user.id:
                await interaction.response.send_message("❌ You already have an open ticket!", ephemeral=True)
                return

        guild = interaction.guild
        if self.trade_type == "Big Trade":
            category = guild.get_channel(CONFIG["BIG_TRADE_CATEGORY_ID"])
        elif self.trade_type == "Massive Trade":
            category = guild.get_channel(CONFIG["MASSIVE_TRADE_CATEGORY_ID"])
        else:
            category = guild.get_channel(CONFIG["TICKET_CATEGORY_ID"])

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        for key in ("MIDDLEMAN_ROLE_ID", "LEAD_COORD_ROLE_ID", "TRUSTED_TRADER_ROLE_ID"):
            role = guild.get_role(CONFIG[key])
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        ticket_channel = await guild.create_text_channel(
            name=f"🎫︱{interaction.user.name}", category=category,
            topic=f"Rick's MM - {self.trade_type}", overwrites=overwrites,
        )
        value_raw = self.trade_value.value.strip()
        embed = discord.Embed(title=f"🎫 Rick's MM Request - {self.trade_type}", description="A middleman will be with you shortly!", color=0xFF6B00, timestamp=datetime.utcnow())
        embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
        embed.add_field(name="👤 Requested by", value=interaction.user.mention, inline=False)
        embed.add_field(name="🤝 Trading with", value=self.trading_with.value, inline=False)
        embed.add_field(name="📦 Trade Details", value=self.trade_details.value, inline=False)
        embed.add_field(name="💰 Estimated Value", value=value_raw, inline=True)
        embed.add_field(name="🔗 Can join links?", value=self.can_join_links.value, inline=True)
        if self.roblox_users.value:
            embed.add_field(name="🎮 Roblox Users", value=self.roblox_users.value, inline=False)
        embed.set_footer(text=f"Rick's MM | Ticket ID: {ticket_channel.id}", icon_url=CONFIG["SERVER_ICON"])

        class TicketActionView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.green, custom_id="claim_ticket", emoji="✋")
            async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.channel.id not in active_tickets:
                    await interaction.response.send_message("❌ Ticket no longer valid!", ephemeral=True)
                    return
                ticket = active_tickets[interaction.channel.id]
                if ticket["claimed_by"]:
                    await interaction.response.send_message("❌ Already claimed!", ephemeral=True)
                    return
                if interaction.user.id == ticket["owner"]:
                    await interaction.response.send_message("❌ You cannot claim your own ticket!", ephemeral=True)
                    return
                claim_role_key = {"Small Trade": "SMALL_TRADE_CLAIM_ROLE_ID", "Big Trade": "BIG_TRADE_CLAIM_ROLE_ID", "Massive Trade": "MASSIVE_TRADE_CLAIM_ROLE_ID"}.get(ticket["type"])
                claim_role = interaction.guild.get_role(CONFIG.get(claim_role_key)) if claim_role_key else None
                if not interaction.user.guild_permissions.administrator and claim_role and claim_role not in interaction.user.roles:
                    await interaction.response.send_message(f"❌ You need the **{claim_role.name}** role!", ephemeral=True)
                    return
                ticket["claimed_by"] = interaction.user.id
                await lock_staff_roles(interaction.channel, interaction.guild)
                await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
                for item in self.children:
                    item.disabled = True
                button.label = "Ticket Claimed"
                await interaction.message.edit(view=self)
                e = discord.Embed(title="✅ Ticket Claimed", description=f"Claimed by {interaction.user.mention}", color=0xFF6B00, timestamp=datetime.utcnow())
                e.set_thumbnail(url=CONFIG["SERVER_ICON"])
                e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
                await interaction.response.send_message(embed=e)

            @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket", emoji="🔒")
            async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.channel.id not in active_tickets:
                    await interaction.response.send_message("❌ Ticket no longer valid!", ephemeral=True)
                    return
                ticket = active_tickets[interaction.channel.id]
                if not interaction.user.guild_permissions.administrator and ticket["claimed_by"] != interaction.user.id and ticket["claimed_by"] is not None:
                    await interaction.response.send_message("❌ Only the middleman who claimed this ticket can close it!", ephemeral=True)
                    return
                await interaction.response.send_message("🔒 Saving transcript and closing in 5 seconds...")
                await save_transcript_and_send(interaction.channel, interaction.user)
                await asyncio.sleep(5)
                if interaction.channel.id in active_tickets:
                    del active_tickets[interaction.channel.id]
                await interaction.channel.delete()

        ping_key = {"Small Trade": "SMALL_TRADE_PING_ROLE_ID", "Big Trade": "BIG_TRADE_PING_ROLE_ID", "Massive Trade": "MASSIVE_TRADE_PING_ROLE_ID"}.get(self.trade_type)
        ping_role = guild.get_role(CONFIG.get(ping_key)) if ping_key else None
        ping_text = f"{interaction.user.mention} {ping_role.mention}" if ping_role else interaction.user.mention
        ticket_msg = await ticket_channel.send(ping_text, embed=embed, view=TicketActionView())

        active_tickets[ticket_channel.id] = {
            "owner": interaction.user.id, "claimed_by": None, "type": self.trade_type,
            "value": 0, "value_raw": value_raw, "created_at": datetime.utcnow(),
            "status": "open", "messages": [], "ticket_message_id": ticket_msg.id,
        }
        lc = bot.get_channel(CONFIG["LOG_CHANNEL_ID"])
        if lc:
            le = discord.Embed(title="🎫 New Ticket Created", color=0xFF6B00, timestamp=datetime.utcnow())
            le.add_field(name="Channel", value=ticket_channel.mention, inline=True)
            le.add_field(name="Created by", value=interaction.user.mention, inline=True)
            le.add_field(name="Trade Type", value=self.trade_type, inline=True)
            le.add_field(name="Trading with", value=self.trading_with.value, inline=True)
            le.add_field(name="Trade Value", value=value_raw, inline=True)
            le.add_field(name="Can join links?", value=self.can_join_links.value, inline=True)
            if self.roblox_users.value:
                le.add_field(name="Roblox Users", value=self.roblox_users.value, inline=False)
            le.set_thumbnail(url=interaction.user.display_avatar.url)
            le.set_footer(text=f"Rick's MM | User ID: {interaction.user.id}", icon_url=CONFIG["SERVER_ICON"])
            await lc.send(embed=le)
        save_tickets_db()
        await interaction.response.send_message(f"✅ Ticket created! Head to {ticket_channel.mention}", ephemeral=True)

# ─────────────────────────────────────────────────────────────────────────────
# SUPPORT TICKET SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

class SupportIssueSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Question",  description="I have a question about the server",    emoji="❓"),
            discord.SelectOption(label="Report a Scammer",  description="Someone tried to scam me",              emoji="🚨"),
            discord.SelectOption(label="Appeal / Unban",    description="I want to appeal a ban or punishment",  emoji="⚖️"),
            discord.SelectOption(label="Staff Report",      description="I want to report a staff member",       emoji="📋"),
            discord.SelectOption(label="Trade Issue",       description="Problem with a trade or middleman",     emoji="💸"),
            discord.SelectOption(label="Other",             description="Something else not listed above",       emoji="📩"),
        ]
        super().__init__(placeholder="📂 Select the reason for your ticket...", options=options, min_values=1, max_values=1, custom_id="support_issue_select")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SupportDetailModal(self.values[0]))

class SupportPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SupportIssueSelect())

class SupportDetailModal(discord.ui.Modal, title="📩 Support Request"):
    def __init__(self, issue_type: str):
        super().__init__()
        self.issue_type = issue_type

    reporting = discord.ui.TextInput(label="Who are you reporting? (if applicable)", placeholder="Username, user ID, or N/A...", required=False, style=discord.TextStyle.short, max_length=200)
    description = discord.ui.TextInput(label="Describe your issue in detail", placeholder="Please provide as much information as possible...", required=True, style=discord.TextStyle.paragraph, max_length=1000)
    evidence = discord.ui.TextInput(label="Evidence / Links (optional)", placeholder="Any screenshots, user IDs, or links...", required=False, style=discord.TextStyle.paragraph, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        for t in active_support_tickets.values():
            if t["owner"] == interaction.user.id:
                await interaction.response.send_message("❌ You already have an open support ticket!", ephemeral=True)
                return

        guild = interaction.guild
        category = guild.get_channel(CONFIG["SUPPORT_CATEGORY_ID"])
        ping_role = guild.get_role(CONFIG["SUPPORT_PING_ROLE_ID"])

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        for key in ("MIDDLEMAN_ROLE_ID", "LEAD_COORD_ROLE_ID", "TRUSTED_TRADER_ROLE_ID", "SUPPORT_PING_ROLE_ID"):
            role = guild.get_role(CONFIG[key])
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        support_channel = await guild.create_text_channel(
            name=f"🎟︱{interaction.user.name}", category=category,
            topic=f"Support — {self.issue_type}", overwrites=overwrites,
        )

        issue_emoji = {"General Question": "❓", "Report a Scammer": "🚨", "Appeal / Unban": "⚖️", "Staff Report": "📋", "Trade Issue": "💸", "Other": "📩"}.get(self.issue_type, "📩")

        embed = discord.Embed(
            title=f"{issue_emoji} Support Ticket — {self.issue_type}",
            description=f"Hey {interaction.user.mention}, our support team will be with you shortly!\n\nPlease be patient and **do not ping staff**. Any staff member can claim this ticket.",
            color=0xFF6B00, timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
        embed.add_field(name="👤 Opened by",   value=interaction.user.mention, inline=True)
        embed.add_field(name="📂 Category",     value=self.issue_type,          inline=True)
        embed.add_field(name="🎭 Status",       value="⏳ Waiting for staff",   inline=True)
        embed.add_field(name="📝 Description",  value=self.description.value,   inline=False)
        if self.reporting.value:
            embed.add_field(name="🎯 Reporting",  value=self.reporting.value,     inline=False)
        if self.evidence.value:
            embed.add_field(name="🔗 Evidence", value=self.evidence.value,      inline=False)
        embed.set_footer(text=f"Rick's MM | Support ID: {support_channel.id}", icon_url=CONFIG["SERVER_ICON"])

        # Store issue type for use in buttons via closure
        issue_type_ref = self.issue_type

        class SupportActionView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, custom_id="support_claim", emoji="✋")
            async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.channel.id not in active_support_tickets:
                    await interaction.response.send_message("❌ Ticket no longer valid!", ephemeral=True)
                    return
                t = active_support_tickets[interaction.channel.id]
                if t["claimed_by"]:
                    claimer = interaction.guild.get_member(t["claimed_by"])
                    await interaction.response.send_message(f"❌ Already claimed by {claimer.mention if claimer else 'someone'}!", ephemeral=True)
                    return
                if interaction.user.id == t["owner"]:
                    await interaction.response.send_message("❌ You cannot claim your own ticket!", ephemeral=True)
                    return
                if not is_staff(interaction.user):
                    await interaction.response.send_message("❌ Only staff members can claim support tickets!", ephemeral=True)
                    return

                t["claimed_by"] = interaction.user.id
                # Update embed to show claimed status
                new_embed = discord.Embed(
                    title=f"{issue_emoji} Support Ticket — {issue_type_ref}",
                    description=f"This ticket is being handled by {interaction.user.mention}.",
                    color=0x00CC44, timestamp=datetime.utcnow()
                )
                new_embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
                owner_m = interaction.guild.get_member(t["owner"])
                new_embed.add_field(name="👤 Opened by",   value=owner_m.mention if owner_m else "Unknown", inline=True)
                new_embed.add_field(name="📂 Category",    value=t["issue"],                                 inline=True)
                new_embed.add_field(name="🎭 Status",      value=f"✅ Claimed by {interaction.user.mention}", inline=True)
                new_embed.set_footer(text=f"Rick's MM | Support ID: {interaction.channel.id}", icon_url=CONFIG["SERVER_ICON"])
                # Disable claim, keep unclaim+close enabled
                for item in self.children:
                    if item.custom_id == "support_claim":
                        item.disabled = True
                        item.label = "Claimed"
                    if item.custom_id == "support_unclaim":
                        item.disabled = False
                await interaction.message.edit(embed=new_embed, view=self)

                e = discord.Embed(title="✅ Support Ticket Claimed", description=f"This ticket has been claimed by {interaction.user.mention}\n\nFeel free to start helping the user!", color=0x00CC44, timestamp=datetime.utcnow())
                e.set_footer(text="Rick's MM | Support", icon_url=CONFIG["SERVER_ICON"])
                await interaction.response.send_message(embed=e)

                lc = interaction.client.get_channel(CONFIG["SUPPORT_LOG_CHANNEL_ID"])
                if lc:
                    owner_m = interaction.guild.get_member(t["owner"])
                    le = discord.Embed(title="✋ Support Ticket Claimed", color=0x00CC44, timestamp=datetime.utcnow())
                    le.add_field(name="Channel",    value=interaction.channel.mention,             inline=True)
                    le.add_field(name="Claimed by", value=interaction.user.mention,                inline=True)
                    le.add_field(name="Opener",     value=owner_m.mention if owner_m else "Unknown", inline=True)
                    le.add_field(name="Category",   value=t["issue"],                              inline=True)
                    le.set_thumbnail(url=interaction.user.display_avatar.url)
                    le.set_footer(text=f"Rick's MM | Support ID: {interaction.channel.id}", icon_url=CONFIG["SERVER_ICON"])
                    await lc.send(embed=le)

            @discord.ui.button(label="Unclaim", style=discord.ButtonStyle.grey, custom_id="support_unclaim", emoji="🔓", disabled=True)
            async def unclaim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.channel.id not in active_support_tickets:
                    await interaction.response.send_message("❌ Ticket no longer valid!", ephemeral=True)
                    return
                t = active_support_tickets[interaction.channel.id]
                # Strict check: only the exact person who claimed it, or admin
                if t["claimed_by"] is None:
                    await interaction.response.send_message("❌ This ticket is not claimed!", ephemeral=True)
                    return
                if interaction.user.id != t["claimed_by"] and not interaction.user.guild_permissions.administrator:
                    claimer = interaction.guild.get_member(t["claimed_by"])
                    await interaction.response.send_message(f"❌ Only {claimer.mention if claimer else 'the claimer'} can unclaim this ticket!", ephemeral=True)
                    return

                old_claimer_id = t["claimed_by"]
                t["claimed_by"] = None

                # Restore embed to unclaimed state
                new_embed = discord.Embed(
                    title=f"{issue_emoji} Support Ticket — {issue_type_ref}",
                    description=f"Hey <@{t['owner']}>, our support team will be with you shortly!\n\nPlease be patient and **do not ping staff**. Any staff member can claim this ticket.",
                    color=0xFF6B00, timestamp=datetime.utcnow()
                )
                new_embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
                owner_m = interaction.guild.get_member(t["owner"])
                new_embed.add_field(name="👤 Opened by",   value=owner_m.mention if owner_m else "Unknown", inline=True)
                new_embed.add_field(name="📂 Category",    value=t["issue"],                                 inline=True)
                new_embed.add_field(name="🎭 Status",      value="⏳ Waiting for staff",                    inline=True)
                new_embed.set_footer(text=f"Rick's MM | Support ID: {interaction.channel.id}", icon_url=CONFIG["SERVER_ICON"])
                # Re-enable claim, disable unclaim
                for item in self.children:
                    if item.custom_id == "support_claim":
                        item.disabled = False
                        item.label = "Claim"
                    if item.custom_id == "support_unclaim":
                        item.disabled = True
                await interaction.message.edit(embed=new_embed, view=self)

                e = discord.Embed(title="🔓 Ticket Unclaimed", description=f"{interaction.user.mention} has unclaimed this ticket.\nAny staff member can now claim it.", color=0xFF6B00, timestamp=datetime.utcnow())
                e.set_footer(text="Rick's MM | Support", icon_url=CONFIG["SERVER_ICON"])
                await interaction.response.send_message(embed=e)

                lc = interaction.client.get_channel(CONFIG["SUPPORT_LOG_CHANNEL_ID"])
                if lc:
                    le = discord.Embed(title="🔓 Support Ticket Unclaimed", color=0xFF6B00, timestamp=datetime.utcnow())
                    le.add_field(name="Channel",      value=interaction.channel.mention, inline=True)
                    le.add_field(name="Unclaimed by", value=interaction.user.mention,    inline=True)
                    le.set_footer(text=f"Rick's MM | Support ID: {interaction.channel.id}", icon_url=CONFIG["SERVER_ICON"])
                    await lc.send(embed=le)

            @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="support_close", emoji="🔒")
            async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.channel.id not in active_support_tickets:
                    await interaction.response.send_message("❌ Ticket no longer valid!", ephemeral=True)
                    return
                t = active_support_tickets[interaction.channel.id]
                if not interaction.user.guild_permissions.administrator and t["claimed_by"] != interaction.user.id and t["claimed_by"] is not None:
                    await interaction.response.send_message("❌ Only the staff who claimed this ticket can close it!", ephemeral=True)
                    return
                # Send close reason modal
                await interaction.response.send_modal(SupportCloseModal(interaction.channel.id))

        ping_text = f"{interaction.user.mention} {ping_role.mention}" if ping_role else interaction.user.mention
        await support_channel.send(ping_text, embed=embed, view=SupportActionView())

        active_support_tickets[support_channel.id] = {
            "owner": interaction.user.id, "claimed_by": None,
            "issue": self.issue_type,
            "created_at": datetime.utcnow(),
        }

        lc = bot.get_channel(CONFIG["SUPPORT_LOG_CHANNEL_ID"])
        if lc:
            le = discord.Embed(title="🎟️ New Support Ticket", color=0xFF6B00, timestamp=datetime.utcnow())
            le.add_field(name="Channel",   value=support_channel.mention,  inline=True)
            le.add_field(name="Opened by", value=interaction.user.mention, inline=True)
            le.add_field(name="Category",  value=self.issue_type,          inline=True)
            le.set_thumbnail(url=interaction.user.display_avatar.url)
            le.set_footer(text=f"Rick's MM | User ID: {interaction.user.id}", icon_url=CONFIG["SERVER_ICON"])
            await lc.send(embed=le)

        save_tickets_db()
        await interaction.response.send_message(f"✅ Your support ticket has been created! Head to {support_channel.mention}", ephemeral=True)


class SupportCloseModal(discord.ui.Modal, title="Close Support Ticket"):
    def __init__(self, channel_id: int):
        super().__init__()
        self.channel_id = channel_id

    close_reason = discord.ui.TextInput(
        label="Reason for closing",
        placeholder="e.g. Issue resolved, No response, Duplicate ticket...",
        required=True, max_length=500, style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        if self.channel_id not in active_support_tickets:
            await interaction.response.send_message("❌ Ticket no longer valid!", ephemeral=True)
            return
        t = active_support_tickets[self.channel_id]

        await interaction.response.send_message(f"🔒 Closing ticket in 5 seconds...\n**Reason:** {self.close_reason.value}")

        # Build transcript
        messages = []
        async for msg in interaction.channel.history(limit=None, oldest_first=True):
            messages.append(msg)
        owner_m = interaction.guild.get_member(t["owner"])
        claimer_m = interaction.guild.get_member(t["claimed_by"]) if t["claimed_by"] else None
        lines = [
            f"Support Transcript — #{interaction.channel.name}",
            f"Opener    : {owner_m.name if owner_m else t['owner']}",
            f"Claimed By: {claimer_m.name if claimer_m else 'Unclaimed'}",
            f"Closed By : {interaction.user.name}",
            f"Category  : {t['issue']}",
            f"Close Reason: {self.close_reason.value}",
            f"Closed At : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", "", "─"*60, ""
        ]
        for msg in messages:
            lines.append(f"[{msg.created_at.strftime('%H:%M:%S')}] {msg.author.name}: {msg.content or '[embed/attachment]'}")
        lines += ["", "─"*60, "Powered by Rick's Middleman"]
        file_obj = discord.File(fp=io.BytesIO("\n".join(lines).encode("utf-8")), filename=f"support-{interaction.channel.id}.txt")

        lc = interaction.client.get_channel(CONFIG["SUPPORT_LOG_CHANNEL_ID"])
        if lc:
            le = discord.Embed(title="🔒 Support Ticket Closed", color=0xFF0000, timestamp=datetime.utcnow())
            le.add_field(name="Channel",      value=interaction.channel.name,                      inline=True)
            le.add_field(name="Opened by",    value=owner_m.mention if owner_m else "Unknown",     inline=True)
            le.add_field(name="Closed by",    value=interaction.user.mention,                      inline=True)
            le.add_field(name="Claimed by",   value=claimer_m.mention if claimer_m else "Unclaimed", inline=True)
            le.add_field(name="Category",     value=t["issue"],                                    inline=True)
            le.add_field(name="Messages",     value=str(len(messages)),                            inline=True)
            le.add_field(name="Close Reason", value=self.close_reason.value,                       inline=False)
            le.set_footer(text=f"Rick's MM | Support ID: {interaction.channel.id}", icon_url=CONFIG["SERVER_ICON"])
            await lc.send(embed=le, file=file_obj)

        await asyncio.sleep(5)
        if self.channel_id in active_support_tickets:
            del active_support_tickets[self.channel_id]
        save_tickets_db()
        await interaction.channel.delete()

# ─────────────────────────────────────────────────────────────────────────────
# INDEX SERVICE SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

INDEX_TYPES = {
    "Rainbow":      {"emoji": "🌈", "description": "Rainbow base",     "color": 0xFF6B6B},
    "Candy":        {"emoji": "🍬", "description": "Candy base",       "color": 0xFF69B4},
    "Radioactive":  {"emoji": "☢️",  "description": "Radioactive base", "color": 0x39FF14},
    "Yinyang":      {"emoji": "☯️",  "description": "Yinyang base",    "color": 0x2C2C2C},
    "Galaxy":       {"emoji": "🌌", "description": "Galaxy base",      "color": 0x6A0DAD},
    "Gold":         {"emoji": "🏆", "description": "Gold base",        "color": 0xFFD700},
    "Diamond":      {"emoji": "💎", "description": "Diamond base",     "color": 0xB9F2FF},
}


class IndexTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=name,
                description=info["description"],
                emoji=info["emoji"],
            )
            for name, info in INDEX_TYPES.items()
        ]
        super().__init__(
            placeholder="💎 Select an index type...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="index_type_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(IndexDetailModal(self.values[0]))


class IndexPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(IndexTypeSelect())


class IndexDetailModal(discord.ui.Modal, title="💎 Index Service Request"):
    def __init__(self, index_type: str):
        super().__init__()
        self.index_type = index_type

    roblox_user = discord.ui.TextInput(
        label="Your Roblox Username",
        placeholder="e.g., Builderman",
        required=True,
        style=discord.TextStyle.short,
        max_length=100,
    )
    details = discord.ui.TextInput(
        label="Additional Details (optional)",
        placeholder="Any extra info about your request...",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction):
        for t in active_index_tickets.values():
            if t["owner"] == interaction.user.id:
                await interaction.response.send_message("❌ You already have an open index ticket!", ephemeral=True)
                return

        guild = interaction.guild
        info = INDEX_TYPES[self.index_type]
        category = guild.get_channel(CONFIG["INDEX_CATEGORY_ID"])
        ping_role = guild.get_role(CONFIG["INDEX_PING_ROLE_ID"])
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, send_messages=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        for key in ("MIDDLEMAN_ROLE_ID", "LEAD_COORD_ROLE_ID", "TRUSTED_TRADER_ROLE_ID"):
            role = guild.get_role(CONFIG[key])
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        if ping_role:
            overwrites[ping_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        index_channel = await guild.create_text_channel(
            name=f"{info['emoji']}︱{interaction.user.name}",
            category=category,
            topic=f"Index Service — {self.index_type}",
            overwrites=overwrites,
        )

        embed = discord.Embed(
            title=f"{info['emoji']} Index Service — {self.index_type}",
            description=f"Hey {interaction.user.mention}, your index request has been received!\n\nOur team will be with you shortly. Please wait patiently.",
            color=info["color"],
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
        embed.add_field(name="👤 Requested by",  value=interaction.user.mention, inline=True)
        embed.add_field(name="💎 Index Type",     value=f"{info['emoji']} {self.index_type} — {info['description']}", inline=True)
        embed.add_field(name="🎮 Roblox User",   value=self.roblox_user.value,  inline=True)
        if self.details.value:
            embed.add_field(name="📝 Details",   value=self.details.value,      inline=False)
        embed.set_footer(text=f"Rick's MM | Index ID: {index_channel.id}", icon_url=CONFIG["SERVER_ICON"])

        class IndexActionView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, custom_id="index_claim", emoji="✋")
            async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.channel.id not in active_index_tickets:
                    await interaction.response.send_message("❌ Ticket no longer valid!", ephemeral=True)
                    return
                t = active_index_tickets[interaction.channel.id]
                if t["claimed_by"]:
                    claimer = interaction.guild.get_member(t["claimed_by"])
                    await interaction.response.send_message(f"❌ Already claimed by {claimer.mention if claimer else 'someone'}!", ephemeral=True)
                    return
                if interaction.user.id == t["owner"]:
                    await interaction.response.send_message("❌ You cannot claim your own ticket!", ephemeral=True)
                    return
                supreme_role = interaction.guild.get_role(CONFIG["SUPREME_ROLE_ID"])
                is_admin = interaction.user.guild_permissions.administrator
                has_supreme = supreme_role in interaction.user.roles if supreme_role else False
                if not is_admin and not has_supreme:
                    await interaction.response.send_message(f"❌ Only **Supreme** staff can claim index tickets!", ephemeral=True)
                    return
                t["claimed_by"] = interaction.user.id
                for item in self.children:
                    if item.custom_id == "index_claim":
                        item.disabled = True
                        item.label = "Claimed"
                    if item.custom_id == "index_unclaim":
                        item.disabled = False
                await interaction.message.edit(view=self)
                e = discord.Embed(title="✅ Index Ticket Claimed", description=f"Claimed by {interaction.user.mention}", color=0x00CC44, timestamp=datetime.utcnow())
                e.set_footer(text="Rick's MM | Index Service", icon_url=CONFIG["SERVER_ICON"])
                await interaction.response.send_message(embed=e)
                lc = interaction.client.get_channel(CONFIG["INDEX_LOG_CHANNEL_ID"])
                if lc:
                    owner_m = interaction.guild.get_member(t["owner"])
                    le = discord.Embed(title="✋ Index Ticket Claimed", color=0x00CC44, timestamp=datetime.utcnow())
                    le.add_field(name="Channel",    value=interaction.channel.mention,               inline=True)
                    le.add_field(name="Claimed by", value=interaction.user.mention,                  inline=True)
                    le.add_field(name="Opener",     value=owner_m.mention if owner_m else "Unknown", inline=True)
                    le.add_field(name="Index Type", value=t["index_type"],                           inline=True)
                    le.set_footer(text=f"Rick's MM | Index ID: {interaction.channel.id}", icon_url=CONFIG["SERVER_ICON"])
                    await lc.send(embed=le)

            @discord.ui.button(label="Unclaim", style=discord.ButtonStyle.grey, custom_id="index_unclaim", emoji="🔓", disabled=True)
            async def unclaim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.channel.id not in active_index_tickets:
                    await interaction.response.send_message("❌ Ticket no longer valid!", ephemeral=True)
                    return
                t = active_index_tickets[interaction.channel.id]
                if t["claimed_by"] != interaction.user.id and not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ You didn't claim this ticket!", ephemeral=True)
                    return
                t["claimed_by"] = None
                for item in self.children:
                    if item.custom_id == "index_claim":
                        item.disabled = False
                        item.label = "Claim"
                    if item.custom_id == "index_unclaim":
                        item.disabled = True
                await interaction.message.edit(view=self)
                e = discord.Embed(title="🔓 Index Ticket Unclaimed", description=f"{interaction.user.mention} unclaimed this ticket. Any Supreme staff can now claim it.", color=0xFF6B00, timestamp=datetime.utcnow())
                e.set_footer(text="Rick's MM | Index Service", icon_url=CONFIG["SERVER_ICON"])
                await interaction.response.send_message(embed=e)

            @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="index_close", emoji="🔒")
            async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.channel.id not in active_index_tickets:
                    await interaction.response.send_message("❌ Ticket no longer valid!", ephemeral=True)
                    return
                t = active_index_tickets[interaction.channel.id]
                if not interaction.user.guild_permissions.administrator and t["claimed_by"] != interaction.user.id and t["claimed_by"] is not None:
                    await interaction.response.send_message("❌ Only the staff who claimed this ticket can close it!", ephemeral=True)
                    return

                channel_id = interaction.channel.id

                async def do_close(inner_interaction: discord.Interaction):
                    if channel_id not in active_index_tickets:
                        return
                    t2 = active_index_tickets[channel_id]
                    messages = []
                    async for msg in inner_interaction.channel.history(limit=None, oldest_first=True):
                        messages.append(msg)
                    owner_m = inner_interaction.guild.get_member(t2["owner"])
                    claimer_m = inner_interaction.guild.get_member(t2["claimed_by"]) if t2["claimed_by"] else None
                    lines = [
                        f"Index Transcript — #{inner_interaction.channel.name}",
                        f"Opener    : {owner_m.name if owner_m else t2['owner']}",
                        f"Claimed By: {claimer_m.name if claimer_m else 'Unclaimed'}",
                        f"Closed By : {inner_interaction.user.name}",
                        f"Index Type: {t2['index_type']}",
                        f"Closed At : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", "", "─"*60, ""
                    ]
                    for msg in messages:
                        lines.append(f"[{msg.created_at.strftime('%H:%M:%S')}] {msg.author.name}: {msg.content or '[embed/attachment]'}")
                    lines += ["", "─"*60, "Powered by Rick's Middleman"]
                    file_obj = discord.File(fp=io.BytesIO("\n".join(lines).encode("utf-8")), filename=f"index-{channel_id}.txt")
                    lc = inner_interaction.client.get_channel(CONFIG["INDEX_LOG_CHANNEL_ID"])
                    if lc:
                        le = discord.Embed(title="🔒 Index Ticket Closed", color=0xFF0000, timestamp=datetime.utcnow())
                        le.add_field(name="Channel",    value=inner_interaction.channel.name,                   inline=True)
                        le.add_field(name="Opened by",  value=owner_m.mention if owner_m else "Unknown",        inline=True)
                        le.add_field(name="Closed by",  value=inner_interaction.user.mention,                   inline=True)
                        le.add_field(name="Claimed by", value=claimer_m.mention if claimer_m else "Unclaimed",  inline=True)
                        le.add_field(name="Index Type", value=t2["index_type"],                                 inline=True)
                        le.add_field(name="Messages",   value=str(len(messages)),                               inline=True)
                        le.set_footer(text=f"Rick's MM | Index ID: {channel_id}", icon_url=CONFIG["SERVER_ICON"])
                        await lc.send(embed=le, file=file_obj)
                    if channel_id in active_index_tickets:
                        del active_index_tickets[channel_id]
                    await inner_interaction.channel.delete()

                class ConfirmCloseView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=30)

                    @discord.ui.button(label="Yes, Close", style=discord.ButtonStyle.red, emoji="✅")
                    async def confirm(self, inner_interaction: discord.Interaction, btn: discord.ui.Button):
                        for item in self.children:
                            item.disabled = True
                        await inner_interaction.message.edit(view=self)
                        await inner_interaction.response.send_message("🔒 Closing index ticket...")
                        await do_close(inner_interaction)

                    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, emoji="❌")
                    async def cancel(self, inner_interaction: discord.Interaction, btn: discord.ui.Button):
                        for item in self.children:
                            item.disabled = True
                        await inner_interaction.message.edit(view=self)
                        await inner_interaction.response.send_message("✅ Close cancelled.", ephemeral=True)

                    async def on_timeout(self):
                        for item in self.children:
                            item.disabled = True
                        try:
                            await self.message.edit(view=self)
                        except:
                            pass

                confirm_embed = discord.Embed(
                    title="🔒 Close Index Ticket?",
                    description="Are you sure you want to close this ticket?\nThis action **cannot be undone**.",
                    color=0xFF6B00
                )
                confirm_embed.set_footer(text="Rick's MM | Prompt expires in 30 seconds", icon_url=CONFIG["SERVER_ICON"])
                view = ConfirmCloseView()
                await interaction.response.send_message(embed=confirm_embed, view=view)
                view.message = await interaction.original_response()

        ping_text = f"{interaction.user.mention} {ping_role.mention}" if ping_role else interaction.user.mention
        await index_channel.send(ping_text, embed=embed, view=IndexActionView())

        active_index_tickets[index_channel.id] = {
            "owner": interaction.user.id,
            "claimed_by": None,
            "index_type": self.index_type,
            "created_at": datetime.utcnow(),
        }

        lc = bot.get_channel(CONFIG["INDEX_LOG_CHANNEL_ID"])
        if lc:
            le = discord.Embed(title="💎 New Index Ticket", color=info["color"], timestamp=datetime.utcnow())
            le.add_field(name="Channel",    value=index_channel.mention,   inline=True)
            le.add_field(name="Opened by",  value=interaction.user.mention, inline=True)
            le.add_field(name="Index Type", value=f"{info['emoji']} {self.index_type}", inline=True)
            le.add_field(name="Roblox User", value=self.roblox_user.value, inline=True)
            le.set_thumbnail(url=interaction.user.display_avatar.url)
            le.set_footer(text=f"Rick's MM | User ID: {interaction.user.id}", icon_url=CONFIG["SERVER_ICON"])
            await lc.send(embed=le)

        save_tickets_db()
        await interaction.response.send_message(f"✅ Your index ticket has been created! Head to {index_channel.mention}", ephemeral=True)


@bot.tree.command(name="indexpanel", description="Post the index service panel")
@app_commands.checks.has_permissions(administrator=True)
async def indexpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="💎 Rick's MM — Index Service",
        description=(
            "**Welcome to Rick's Index Service!**\n\n"
            "We offer indexing services for a variety of base types.\n\n"
            "**📋 Available Index Types:**\n"
            "🌈 **Rainbow** — Rainbow base\n"
            "🍬 **Candy** — Candy base\n"
            "☢️ **Radioactive** — Radioactive base\n"
            "☯️ **Yinyang** — Yinyang base\n"
            "🌌 **Galaxy** — Galaxy base\n"
            "🏆 **Gold** — Gold base\n"
            "💎 **Diamond** — Diamond base\n\n"
            "Simply choose an option from the dropdown to create a ticket!"
        ),
        color=0xFF6B00,
    )
    embed.set_image(url=CONFIG["SERVER_BANNER"])
    embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
    embed.set_footer(text="🔒 Rick's MM | Index Service • Fast & Reliable", icon_url=CONFIG["SERVER_ICON"])
    await interaction.channel.send(embed=embed, view=IndexPanelView())
    await interaction.response.send_message("✅ Index panel posted!", ephemeral=True)

@indexpanel.error
async def indexpanel_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ You need **Administrator** permissions!", ephemeral=True)


# ─────────────────────────────────────────────────────────────────────────────
# PERSISTENT VIEWS (survive bot restarts)
# ─────────────────────────────────────────────────────────────────────────────

class TicketActionViewPersistent(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.green, custom_id="claim_ticket", emoji="✋")
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id not in active_tickets:
            await interaction.response.send_message("❌ Ticket not found in database!", ephemeral=True)
            return
        ticket = active_tickets[interaction.channel.id]
        if ticket["claimed_by"]:
            await interaction.response.send_message("❌ Already claimed!", ephemeral=True)
            return
        if interaction.user.id == ticket["owner"]:
            await interaction.response.send_message("❌ You cannot claim your own ticket!", ephemeral=True)
            return
        claim_role_key = {"Small Trade": "SMALL_TRADE_CLAIM_ROLE_ID", "Big Trade": "BIG_TRADE_CLAIM_ROLE_ID", "Massive Trade": "MASSIVE_TRADE_CLAIM_ROLE_ID"}.get(ticket["type"])
        claim_role = interaction.guild.get_role(CONFIG.get(claim_role_key)) if claim_role_key else None
        if not interaction.user.guild_permissions.administrator and claim_role and claim_role not in interaction.user.roles:
            await interaction.response.send_message(f"❌ You need the **{claim_role.name}** role!", ephemeral=True)
            return
        ticket["claimed_by"] = interaction.user.id
        await lock_staff_roles(interaction.channel, interaction.guild)
        await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
        for item in self.children:
            item.disabled = True
        button.label = "Ticket Claimed"
        await interaction.message.edit(view=self)
        e = discord.Embed(title="✅ Ticket Claimed", description=f"Claimed by {interaction.user.mention}", color=0xFF6B00, timestamp=datetime.utcnow())
        e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
        await interaction.response.send_message(embed=e)
        save_tickets_db()

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket", emoji="🔒")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id not in active_tickets:
            await interaction.response.send_message("❌ Ticket not found in database!", ephemeral=True)
            return
        ticket = active_tickets[interaction.channel.id]
        if not interaction.user.guild_permissions.administrator and ticket["claimed_by"] != interaction.user.id and ticket["claimed_by"] is not None:
            await interaction.response.send_message("❌ Only the middleman who claimed this ticket can close it!", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Saving transcript and closing in 5 seconds...")
        await save_transcript_and_send(interaction.channel, interaction.user)
        await asyncio.sleep(5)
        if interaction.channel.id in active_tickets:
            del active_tickets[interaction.channel.id]
        save_tickets_db()
        await interaction.channel.delete()


class SupportActionViewPersistent(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, custom_id="support_claim", emoji="✋")
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id not in active_support_tickets:
            await interaction.response.send_message("❌ Ticket not found in database!", ephemeral=True)
            return
        t = active_support_tickets[interaction.channel.id]
        if t["claimed_by"]:
            claimer = interaction.guild.get_member(t["claimed_by"])
            await interaction.response.send_message(f"❌ Already claimed by {claimer.mention if claimer else 'someone'}!", ephemeral=True)
            return
        if interaction.user.id == t["owner"]:
            await interaction.response.send_message("❌ You cannot claim your own ticket!", ephemeral=True)
            return
        if not is_staff(interaction.user):
            await interaction.response.send_message("❌ Only staff can claim support tickets!", ephemeral=True)
            return
        t["claimed_by"] = interaction.user.id
        for item in self.children:
            if item.custom_id == "support_claim":
                item.disabled = True
                item.label = "Claimed"
            if item.custom_id == "support_unclaim":
                item.disabled = False
        await interaction.message.edit(view=self)
        e = discord.Embed(title="✅ Support Ticket Claimed", description=f"Claimed by {interaction.user.mention}", color=0x00CC44, timestamp=datetime.utcnow())
        e.set_footer(text="Rick's MM | Support", icon_url=CONFIG["SERVER_ICON"])
        await interaction.response.send_message(embed=e)
        save_tickets_db()

    @discord.ui.button(label="Unclaim", style=discord.ButtonStyle.grey, custom_id="support_unclaim", emoji="🔓", disabled=True)
    async def unclaim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id not in active_support_tickets:
            await interaction.response.send_message("❌ Ticket not found in database!", ephemeral=True)
            return
        t = active_support_tickets[interaction.channel.id]
        if t["claimed_by"] is None:
            await interaction.response.send_message("❌ This ticket is not claimed!", ephemeral=True)
            return
        if interaction.user.id != t["claimed_by"] and not interaction.user.guild_permissions.administrator:
            claimer = interaction.guild.get_member(t["claimed_by"])
            await interaction.response.send_message(f"❌ Only {claimer.mention if claimer else 'the claimer'} can unclaim this ticket!", ephemeral=True)
            return
        t["claimed_by"] = None
        for item in self.children:
            if item.custom_id == "support_claim":
                item.disabled = False
                item.label = "Claim"
            if item.custom_id == "support_unclaim":
                item.disabled = True
        await interaction.message.edit(view=self)
        e = discord.Embed(title="🔓 Ticket Unclaimed", description=f"{interaction.user.mention} unclaimed this ticket.", color=0xFF6B00, timestamp=datetime.utcnow())
        e.set_footer(text="Rick's MM | Support", icon_url=CONFIG["SERVER_ICON"])
        await interaction.response.send_message(embed=e)
        save_tickets_db()

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="support_close", emoji="🔒")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id not in active_support_tickets:
            await interaction.response.send_message("❌ Ticket not found in database!", ephemeral=True)
            return
        t = active_support_tickets[interaction.channel.id]
        if not interaction.user.guild_permissions.administrator and t["claimed_by"] != interaction.user.id and t["claimed_by"] is not None:
            await interaction.response.send_message("❌ Only the staff who claimed this ticket can close it!", ephemeral=True)
            return
        await interaction.response.send_modal(SupportCloseModal(interaction.channel.id))


class IndexActionViewPersistent(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, custom_id="index_claim", emoji="✋")
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id not in active_index_tickets:
            await interaction.response.send_message("❌ Ticket not found in database!", ephemeral=True)
            return
        t = active_index_tickets[interaction.channel.id]
        if t["claimed_by"]:
            claimer = interaction.guild.get_member(t["claimed_by"])
            await interaction.response.send_message(f"❌ Already claimed by {claimer.mention if claimer else 'someone'}!", ephemeral=True)
            return
        if interaction.user.id == t["owner"]:
            await interaction.response.send_message("❌ You cannot claim your own ticket!", ephemeral=True)
            return
        supreme_role = interaction.guild.get_role(CONFIG["SUPREME_ROLE_ID"])
        if not interaction.user.guild_permissions.administrator and (not supreme_role or supreme_role not in interaction.user.roles):
            await interaction.response.send_message("❌ Only **Supreme** staff can claim index tickets!", ephemeral=True)
            return
        t["claimed_by"] = interaction.user.id
        for item in self.children:
            if item.custom_id == "index_claim":
                item.disabled = True
                item.label = "Claimed"
            if item.custom_id == "index_unclaim":
                item.disabled = False
        await interaction.message.edit(view=self)
        e = discord.Embed(title="✅ Index Ticket Claimed", description=f"Claimed by {interaction.user.mention}", color=0x00CC44, timestamp=datetime.utcnow())
        e.set_footer(text="Rick's MM | Index Service", icon_url=CONFIG["SERVER_ICON"])
        await interaction.response.send_message(embed=e)
        save_tickets_db()

    @discord.ui.button(label="Unclaim", style=discord.ButtonStyle.grey, custom_id="index_unclaim", emoji="🔓", disabled=True)
    async def unclaim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id not in active_index_tickets:
            await interaction.response.send_message("❌ Ticket not found in database!", ephemeral=True)
            return
        t = active_index_tickets[interaction.channel.id]
        if t["claimed_by"] != interaction.user.id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You didn't claim this ticket!", ephemeral=True)
            return
        t["claimed_by"] = None
        for item in self.children:
            if item.custom_id == "index_claim":
                item.disabled = False
                item.label = "Claim"
            if item.custom_id == "index_unclaim":
                item.disabled = True
        await interaction.message.edit(view=self)
        e = discord.Embed(title="🔓 Index Ticket Unclaimed", description=f"{interaction.user.mention} unclaimed this ticket.", color=0xFF6B00, timestamp=datetime.utcnow())
        e.set_footer(text="Rick's MM | Index Service", icon_url=CONFIG["SERVER_ICON"])
        await interaction.response.send_message(embed=e)
        save_tickets_db()

    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="index_close", emoji="🔒")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id not in active_index_tickets:
            await interaction.response.send_message("❌ Ticket not found in database!", ephemeral=True)
            return
        t = active_index_tickets[interaction.channel.id]
        if not interaction.user.guild_permissions.administrator and t["claimed_by"] != interaction.user.id and t["claimed_by"] is not None:
            await interaction.response.send_message("❌ Only the staff who claimed this ticket can close it!", ephemeral=True)
            return
        channel_id = interaction.channel.id

        async def do_close(inner_interaction: discord.Interaction):
            if channel_id not in active_index_tickets:
                return
            t2 = active_index_tickets[channel_id]
            messages = []
            async for msg in inner_interaction.channel.history(limit=None, oldest_first=True):
                messages.append(msg)
            owner_m = inner_interaction.guild.get_member(t2["owner"])
            claimer_m = inner_interaction.guild.get_member(t2["claimed_by"]) if t2["claimed_by"] else None
            lines = [
                f"Index Transcript — #{inner_interaction.channel.name}",
                f"Opener    : {owner_m.name if owner_m else t2['owner']}",
                f"Claimed By: {claimer_m.name if claimer_m else 'Unclaimed'}",
                f"Closed By : {inner_interaction.user.name}",
                f"Index Type: {t2['index_type']}",
                f"Closed At : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", "", "─"*60, ""
            ]
            for msg in messages:
                lines.append(f"[{msg.created_at.strftime('%H:%M:%S')}] {msg.author.name}: {msg.content or '[embed/attachment]'}")
            lines += ["", "─"*60, "Powered by Rick's Middleman"]
            file_obj = discord.File(fp=io.BytesIO("\n".join(lines).encode("utf-8")), filename=f"index-{channel_id}.txt")
            lc = inner_interaction.client.get_channel(CONFIG["INDEX_LOG_CHANNEL_ID"])
            if lc:
                le = discord.Embed(title="🔒 Index Ticket Closed", color=0xFF0000, timestamp=datetime.utcnow())
                le.add_field(name="Channel",    value=inner_interaction.channel.name,                  inline=True)
                le.add_field(name="Opened by",  value=owner_m.mention if owner_m else "Unknown",       inline=True)
                le.add_field(name="Closed by",  value=inner_interaction.user.mention,                  inline=True)
                le.add_field(name="Claimed by", value=claimer_m.mention if claimer_m else "Unclaimed", inline=True)
                le.add_field(name="Index Type", value=t2["index_type"],                                inline=True)
                le.add_field(name="Messages",   value=str(len(messages)),                              inline=True)
                le.set_footer(text=f"Rick's MM | Index ID: {channel_id}", icon_url=CONFIG["SERVER_ICON"])
                await lc.send(embed=le, file=file_obj)
            if channel_id in active_index_tickets:
                del active_index_tickets[channel_id]
            save_tickets_db()
            await inner_interaction.channel.delete()

        class ConfirmCloseView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(label="Yes, Close", style=discord.ButtonStyle.red, emoji="✅")
            async def confirm(self, inner_interaction: discord.Interaction, btn: discord.ui.Button):
                for item in self.children:
                    item.disabled = True
                await inner_interaction.message.edit(view=self)
                await inner_interaction.response.send_message("🔒 Closing index ticket...")
                await do_close(inner_interaction)

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, emoji="❌")
            async def cancel(self, inner_interaction: discord.Interaction, btn: discord.ui.Button):
                for item in self.children:
                    item.disabled = True
                await inner_interaction.message.edit(view=self)
                await inner_interaction.response.send_message("✅ Close cancelled.", ephemeral=True)

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                try:
                    await self.message.edit(view=self)
                except:
                    pass

        confirm_embed = discord.Embed(title="🔒 Close Index Ticket?", description="Are you sure you want to close this ticket?\nThis action **cannot be undone**.", color=0xFF6B00)
        confirm_embed.set_footer(text="Rick's MM | Prompt expires in 30 seconds", icon_url=CONFIG["SERVER_ICON"])
        view = ConfirmCloseView()
        await interaction.response.send_message(embed=confirm_embed, view=view)
        view.message = await interaction.original_response()


@bot.event
async def on_ready():
    print(f'🚀 {bot.user} is now online!')
    bot.add_view(TradeTypeView())
    bot.add_view(SupportPanelView())
    bot.add_view(IndexPanelView())
    # Persistent views for ticket buttons (survive restarts)
    bot.add_view(TicketActionViewPersistent())
    bot.add_view(SupportActionViewPersistent())
    bot.add_view(IndexActionViewPersistent())
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Error syncing: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return
    if message.author.id in afk_users:
        afk_info = afk_users.pop(message.author.id)
        mins = int((datetime.utcnow() - afk_info["time"]).total_seconds() // 60)
        e = discord.Embed(description=f"✅ Welcome back {message.author.mention}! You were AFK for **{mins}** minute(s).", color=0xFF6B00)
        e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
        await message.channel.send(embed=e, delete_after=8)
    for mentioned in message.mentions:
        if mentioned.id in afk_users and mentioned.id != message.author.id:
            e = discord.Embed(description=f"💤 {mentioned.mention} is AFK: **{afk_users[mentioned.id]['reason']}**", color=0xFF6B00)
            e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
            await message.channel.send(embed=e, delete_after=8)
    if message.content.startswith("+afk"):
        message.content = ".afk " + message.content[4:].strip()
        ctx = await bot.get_context(message)
        if ctx.command:
            await bot.invoke(ctx)
        return
    if message.content.startswith("+w"):
        message.content = ".w " + message.content[2:].strip()
        ctx = await bot.get_context(message)
        if ctx.command:
            await bot.invoke(ctx)
        return
    await bot.process_commands(message)

# ─────────────────────────────────────────────────────────────────────────────
# SLASH COMMANDS
# ─────────────────────────────────────────────────────────────────────────────

@bot.tree.command(name="panel", description="Post Rick's MM middleman request panel")
@app_commands.checks.has_permissions(administrator=True)
async def panel(interaction: discord.Interaction):
    embed = discord.Embed(title="🛡️ Rick's MM Service", description="**Welcome to Rick's Middleman Service!**\n\nOpen a ticket to request a verified middleman for your Roblox trades.\n\n**Why use Rick's MM?**\n✅ Trusted and verified staff\n✅ Fast response times\n✅ 100% secure transactions\n✅ Professional service\n\n**Select your trade size below to get started! 👇**", color=0xFF6B00)
    embed.set_image(url=CONFIG["SERVER_BANNER"])
    embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
    embed.set_footer(text="🔒 Rick's MM | Your safety is our priority", icon_url=CONFIG["SERVER_ICON"])
    await interaction.channel.send(embed=embed, view=TradeTypeView())
    await interaction.response.send_message("✅ Panel posted!", ephemeral=True)

@panel.error
async def panel_error(interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ You need **Administrator** permissions!", ephemeral=True)


@bot.tree.command(name="supportpanel", description="Post the support ticket panel")
@app_commands.checks.has_permissions(administrator=True)
async def supportpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎟️ Rick's MM — Support Center",
        description=(
            "**Need help? We're here for you.**\n\n"
            "Our support team handles all issues quickly and professionally.\n\n"
            "**📂 What we can help with:**\n"
            "❓ **General Questions** — Server info, how things work\n"
            "🚨 **Report a Scammer** — Someone tried to scam you\n"
            "⚖️ **Appeals / Unbans** — Contest a punishment\n"
            "📋 **Staff Reports** — Report misconduct\n"
            "💸 **Trade Issues** — Problems with a middleman trade\n"
            "📩 **Other** — Anything else\n\n"
            "**📌 Before opening a ticket:**\n"
            "• Check the rules and FAQ channels first\n"
            "• Do **not** ping staff directly\n"
            "• Be ready to provide evidence if needed\n\n"
            "**👇 Select a category below to open a ticket**"
        ),
        color=0xFF6B00,
    )
    embed.set_image(url=CONFIG["SERVER_BANNER"])
    embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
    embed.set_footer(text="🔒 Rick's MM | Support Center • We respond as fast as possible", icon_url=CONFIG["SERVER_ICON"])
    await interaction.channel.send(embed=embed, view=SupportPanelView())
    await interaction.response.send_message("✅ Support panel posted!", ephemeral=True)

@supportpanel.error
async def supportpanel_error(interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ You need **Administrator** permissions!", ephemeral=True)


@bot.tree.command(name="rules", description="Display server rules")
async def rules(interaction: discord.Interaction):
    embed = discord.Embed(title="📋 Server Rules", description="**Welcome to Rick's MM! 🎭**\n\nPlease follow these rules to keep our community safe.", color=0xFF6B00, timestamp=datetime.utcnow())
    embed.set_image(url=CONFIG["SERVER_BANNER"])
    for rule in SERVER_RULES:
        embed.add_field(name=f"{rule['number']}. {rule['title']}", value=rule['description'], inline=False)
    embed.add_field(name="⚠️ Important", value="Breaking rules may result in warnings, mutes, or bans.", inline=False)
    embed.set_thumbnail(url=CONFIG["SERVER_ICON"])
    embed.set_footer(text="Rick's MM | Stay Safe, Trade Smart", icon_url=CONFIG["SERVER_ICON"])
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ Rules posted!", ephemeral=True)


@bot.tree.command(name="add", description="Add a user to the ticket")
async def add_user(interaction: discord.Interaction, user: discord.Member):
    if interaction.channel.id not in active_tickets and interaction.channel.id not in active_support_tickets:
        await interaction.response.send_message("❌ This is not a ticket channel!", ephemeral=True)
        return
    await interaction.channel.set_permissions(user, view_channel=True, send_messages=True)
    e = discord.Embed(description=f"✅ Added {user.mention} to the ticket!", color=0xFF6B00)
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await interaction.response.send_message(embed=e)


@bot.tree.command(name="close", description="Close and delete the MM ticket (saves transcript)")
async def close_ticket(interaction: discord.Interaction):
    if interaction.channel.id not in active_tickets:
        await interaction.response.send_message("❌ This is not a MM ticket channel! Use the **Close** button inside support tickets.", ephemeral=True)
        return
    ticket = active_tickets[interaction.channel.id]
    if not interaction.user.guild_permissions.administrator and ticket["claimed_by"] != interaction.user.id and ticket["claimed_by"] is not None:
        await interaction.response.send_message("❌ Only the middleman who claimed this ticket can close it!", ephemeral=True)
        return
    e = discord.Embed(description="🔒 Saving transcript and closing in 5 seconds...", color=0xFF6B00)
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await interaction.response.send_message(embed=e)
    await save_transcript_and_send(interaction.channel, interaction.user)
    await asyncio.sleep(5)
    lc = bot.get_channel(CONFIG["LOG_CHANNEL_ID"])
    if lc:
        owner = interaction.guild.get_member(ticket["owner"])
        le = discord.Embed(title="🔒 Ticket Closed", color=0xFF6B00, timestamp=datetime.utcnow())
        le.add_field(name="Channel", value=interaction.channel.name, inline=True)
        le.add_field(name="Ticket Owner", value=owner.mention if owner else "Unknown", inline=True)
        le.add_field(name="Closed by", value=interaction.user.mention, inline=True)
        le.add_field(name="Trade Type", value=ticket["type"], inline=True)
        le.add_field(name="Trade Value", value=str(ticket.get('value_raw', 'N/A')), inline=True)
        le.set_footer(text=f"Rick's MM | Ticket ID: {interaction.channel.id}", icon_url=CONFIG["SERVER_ICON"])
        await lc.send(embed=le)
    del active_tickets[interaction.channel.id]
    save_tickets_db()
    await interaction.channel.delete()


@bot.tree.command(name="claim", description="Claim a ticket")
async def claim_ticket(interaction: discord.Interaction):
    if interaction.channel.id not in active_tickets:
        await interaction.response.send_message("❌ This is not a ticket channel!", ephemeral=True)
        return
    ticket = active_tickets[interaction.channel.id]
    if ticket["claimed_by"]:
        await interaction.response.send_message("❌ This ticket is already claimed!", ephemeral=True)
        return
    if interaction.user.id == ticket["owner"]:
        await interaction.response.send_message("❌ You cannot claim your own ticket!", ephemeral=True)
        return
    claim_role_key = {"Small Trade": "SMALL_TRADE_CLAIM_ROLE_ID", "Big Trade": "BIG_TRADE_CLAIM_ROLE_ID", "Massive Trade": "MASSIVE_TRADE_CLAIM_ROLE_ID"}.get(ticket["type"])
    claim_role = interaction.guild.get_role(CONFIG.get(claim_role_key)) if claim_role_key else None
    if not interaction.user.guild_permissions.administrator and claim_role and claim_role not in interaction.user.roles:
        await interaction.response.send_message(f"❌ You need the **{claim_role.name}** role!", ephemeral=True)
        return
    ticket["claimed_by"] = interaction.user.id
    await lock_staff_roles(interaction.channel, interaction.guild)
    await interaction.channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
    e = discord.Embed(title="✅ Ticket Claimed", description=f"Claimed by {interaction.user.mention}", color=0xFF6B00, timestamp=datetime.utcnow())
    e.set_thumbnail(url=CONFIG["SERVER_ICON"])
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await interaction.response.send_message(embed=e)
    lc = bot.get_channel(CONFIG["LOG_CHANNEL_ID"])
    if lc:
        owner = interaction.guild.get_member(ticket["owner"])
        le = discord.Embed(title="✋ Ticket Claimed", color=0xFF6B00, timestamp=datetime.utcnow())
        le.add_field(name="Channel", value=interaction.channel.mention, inline=True)
        le.add_field(name="Claimed by", value=interaction.user.mention, inline=True)
        le.add_field(name="Ticket Owner", value=owner.mention if owner else "Unknown", inline=True)
        le.add_field(name="Trade Value", value=str(ticket.get('value_raw', 'N/A')), inline=True)
        le.set_footer(text=f"Rick's MM | Ticket ID: {interaction.channel.id}", icon_url=CONFIG["SERVER_ICON"])
        await lc.send(embed=le)


@bot.tree.command(name="unclaim", description="Unclaim a ticket")
async def unclaim_ticket(interaction: discord.Interaction):
    if interaction.channel.id not in active_tickets:
        await interaction.response.send_message("❌ This is not a ticket channel!", ephemeral=True)
        return
    ticket = active_tickets[interaction.channel.id]
    if ticket["claimed_by"] != interaction.user.id and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You haven't claimed this ticket!", ephemeral=True)
        return
    old_claimer_id = ticket["claimed_by"]
    ticket["claimed_by"] = None
    await unlock_staff_roles(interaction.channel, interaction.guild)
    if old_claimer_id:
        old_claimer = interaction.guild.get_member(old_claimer_id)
        if old_claimer:
            await interaction.channel.set_permissions(old_claimer, overwrite=None)
    # Re-enable buttons on the original ticket message
    ticket_msg_id = ticket.get("ticket_message_id")
    if ticket_msg_id:
        try:
            ticket_msg = await interaction.channel.fetch_message(ticket_msg_id)
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Claim Ticket", style=discord.ButtonStyle.green, emoji="✋", custom_id="claim_ticket"))
            view.add_item(discord.ui.Button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket"))
            await ticket_msg.edit(view=view)
        except Exception as ex:
            print(f"Could not re-enable buttons: {ex}")
    e = discord.Embed(title="🔓 Ticket Unclaimed", description=f"{interaction.user.mention} has unclaimed this ticket. Any staff can now claim it.", color=0xFF6B00, timestamp=datetime.utcnow())
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await interaction.response.send_message(embed=e)


@bot.tree.command(name="transcript", description="Manually generate a transcript")
async def transcript_command(interaction: discord.Interaction):
    if interaction.channel.id not in active_tickets:
        await interaction.response.send_message("❌ This is not a ticket channel!", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await save_transcript_and_send(interaction.channel, interaction.user)
    await interaction.followup.send("✅ Transcript saved!", ephemeral=True)


@bot.tree.command(name="rename", description="Rename the ticket channel")
async def rename_ticket(interaction: discord.Interaction, new_name: str):
    if interaction.channel.id not in active_tickets and interaction.channel.id not in active_support_tickets:
        await interaction.response.send_message("❌ This is not a ticket channel!", ephemeral=True)
        return
    old_name = interaction.channel.name
    prefix = "🎫︱" if interaction.channel.id in active_tickets else "🎟︱"
    await interaction.channel.edit(name=f"{prefix}{new_name}")
    e = discord.Embed(description=f"✅ Renamed from `{old_name}` to `{prefix}{new_name}`", color=0xFF6B00)
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await interaction.response.send_message(embed=e)


@bot.tree.command(name="transfer", description="Transfer ticket to another middleman")
async def transfer(interaction: discord.Interaction, middleman: discord.Member):
    if interaction.channel.id not in active_tickets:
        await interaction.response.send_message("❌ This is not a ticket channel!", ephemeral=True)
        return
    ticket = active_tickets[interaction.channel.id]
    old_claimer = interaction.guild.get_member(ticket["claimed_by"]) if ticket["claimed_by"] else None
    ticket["claimed_by"] = middleman.id
    await interaction.channel.set_permissions(middleman, view_channel=True, send_messages=True)
    e = discord.Embed(title="🔄 Ticket Transferred", description=f"Transferred to {middleman.mention}.", color=0xFF6B00, timestamp=datetime.utcnow())
    e.add_field(name="Transferred by", value=interaction.user.mention, inline=True)
    e.add_field(name="Previous MM", value=old_claimer.mention if old_claimer else "Unclaimed", inline=True)
    e.add_field(name="New MM", value=middleman.mention, inline=True)
    e.set_thumbnail(url=CONFIG["SERVER_ICON"])
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await interaction.response.send_message(embed=e)


@bot.tree.command(name="manageban", description="Ban or unban a user")
@app_commands.describe(target="The user", action="Ban or unban", reason="Reason")
@app_commands.choices(action=[app_commands.Choice(name="ban", value="ban"), app_commands.Choice(name="unban", value="unban")])
async def manageban(interaction: discord.Interaction, target: discord.User, action: app_commands.Choice[str], reason: str = "No reason provided"):
    ban_role = interaction.guild.get_role(CONFIG.get("BAN_PERMS_ROLE_ID"))
    if not interaction.user.guild_permissions.administrator and (not ban_role or ban_role not in interaction.user.roles):
        await interaction.response.send_message("❌ You need the **Ban Perms** role!", ephemeral=True)
        return
    if action.value == "ban":
        try:
            await interaction.guild.ban(target, reason=reason, delete_message_days=0)
            color, emoji, action_text = discord.Color.red(), "🔨", "Banned"
        except (discord.Forbidden, discord.HTTPException) as ex:
            await interaction.response.send_message(f"❌ Failed: {ex}", ephemeral=True); return
    else:
        try:
            await interaction.guild.unban(target, reason=reason)
            color, emoji, action_text = discord.Color.green(), "✅", "Unbanned"
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as ex:
            await interaction.response.send_message(f"❌ Failed: {ex}", ephemeral=True); return
    e = discord.Embed(title=f"{emoji} User {action_text}", description=f"{target.mention} has been **{action_text.lower()}**.", color=color, timestamp=datetime.utcnow())
    e.add_field(name="User", value=f"{target} (`{target.id}`)", inline=True)
    e.add_field(name="Moderator", value=interaction.user.mention, inline=True)
    e.add_field(name="Reason", value=reason, inline=False)
    e.set_thumbnail(url=target.display_avatar.url)
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await interaction.response.send_message(embed=e)
    lc = bot.get_channel(CONFIG["LOG_CHANNEL_ID"])
    if lc:
        await lc.send(embed=e)


@bot.tree.command(name="middleman1", description="Show how middleman trades work")
async def middleman1(interaction: discord.Interaction):
    e = discord.Embed(title="How Middleman Trades Work", description="• A middleman is a trusted go-between who holds payment until the seller delivers goods or services.\n• The funds are released once the buyer confirms everything is as agreed.\n• This process helps prevent scams, build trust, and resolve disputes.\n• Common in valuable games, real-life money trades, in-game currency, and collectibles.\n• Only works safely if the middleman is reputable and verified.", color=0xFF6B00)
    e.set_image(url="https://media.discordapp.net/attachments/1419476852765884619/1448418105041752086/middleman1_2.webp?ex=6994d5fa&is=6993847a&hm=b9ae314b546ed7e4b0f817f694f976155d39a6556af80a6ccaaff8949dc221d4&=&format=webp&width=587&height=451")
    e.set_footer(text="Powered by Rick's Middleman", icon_url=CONFIG["SERVER_ICON"])
    await interaction.channel.send(embed=e)
    await interaction.response.send_message("✅ Posted!", ephemeral=True)


@bot.tree.command(name="middleman2", description="Show how mutual trades work")
async def middleman2(interaction: discord.Interaction):
    e = discord.Embed(title="How Mutual Trades Work via Middleman", description="• A middleman is a trusted go-between who receives items from both parties.\n• Once verified, the middleman distributes the items to each party as agreed.\n• This process ensures fairness and prevents scams.\n• Common in mutual trades, swaps, and high-value exchanges.\n• Only works safely if the middleman is reputable and verified.", color=0xFF6B00)
    e.set_image(url="https://media.discordapp.net/attachments/1419476852765884619/1448418858716102696/middleman2_1.webp?ex=6994d6ae&is=6993852e&hm=e02d51aaa3f9c2083856d4c279be2715bbc3defc22ce53562ff1d868a54ce7a3&=&format=webp&width=611&height=342")
    e.set_footer(text="Powered by Rick's Middleman", icon_url=CONFIG["SERVER_ICON"])
    await interaction.channel.send(embed=e)
    await interaction.response.send_message("✅ Posted!", ephemeral=True)

# ─────────────────────────────────────────────────────────────────────────────
# PREFIX COMMANDS
# ─────────────────────────────────────────────────────────────────────────────

@bot.command(name="afk")
async def afk(ctx, *, reason: str = "AFK"):
    afk_users[ctx.author.id] = {"reason": reason, "time": datetime.utcnow()}
    e = discord.Embed(description=f"💤 {ctx.author.mention} is now AFK: **{reason}**", color=0xFF6B00)
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await ctx.send(embed=e)


@bot.command(name="w", aliases=["whois"])
async def whois(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    key_perms = []
    perms = member.guild_permissions
    if perms.administrator: key_perms.append("Administrator")
    if perms.ban_members: key_perms.append("Ban Members")
    if perms.kick_members: key_perms.append("Kick Members")
    if perms.manage_guild: key_perms.append("Manage Server")
    if perms.manage_roles: key_perms.append("Manage Roles")
    if perms.manage_channels: key_perms.append("Manage Channels")
    if perms.manage_messages: key_perms.append("Manage Messages")
    if perms.mention_everyone: key_perms.append("Mention Everyone")
    if perms.moderate_members: key_perms.append("Timeout Members")
    roles = [r for r in reversed(member.roles) if r.name != "@everyone"]
    roles_str = " ".join(r.mention for r in roles) if roles else "None"
    vouches = vouch_data.get(member.id, {}).get("count", 0)
    color = member.top_role.color if member.top_role.name != "@everyone" else discord.Color(0xFF6B00)
    e = discord.Embed(color=color, timestamp=datetime.utcnow())
    e.set_author(name=str(member), icon_url=member.display_avatar.url)
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="Joined", value=f"<t:{int(member.joined_at.timestamp())}:F>" if member.joined_at else "Unknown", inline=True)
    e.add_field(name="Registered", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=True)
    e.add_field(name="Vouches", value=f"⭐ {vouches}", inline=True)
    if member.id in afk_users:
        e.add_field(name="AFK", value=afk_users[member.id]["reason"], inline=True)
    e.add_field(name=f"Roles [{len(roles)}]", value=roles_str[:1024], inline=False)
    e.add_field(name="Key Permissions", value=", ".join(key_perms) if key_perms else "None", inline=False)
    e.set_footer(text="Rick's MM | ID: " + str(member.id), icon_url=CONFIG["SERVER_ICON"])
    await ctx.send(embed=e)


vouch_data = load_vouch_data()
vouch_channel_id = None

class SetVouchModal(discord.ui.Modal, title="Set Vouch"):
    user_id = discord.ui.TextInput(label="User ID", placeholder="Enter user ID...", required=True, style=discord.TextStyle.short)
    vouched_by_id = discord.ui.TextInput(label="Vouched By User ID", placeholder="Enter voucher's user ID...", required=True, style=discord.TextStyle.short)
    amount = discord.ui.TextInput(label="Vouch Amount (leave empty = 1)", placeholder="e.g., 1", required=False, style=discord.TextStyle.short)
    star_rate = discord.ui.TextInput(label="Star Rating (1-5)", placeholder="5", required=True, style=discord.TextStyle.short)
    review = discord.ui.TextInput(label="Review", placeholder="Enter review...", required=True, style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            uid = int(self.user_id.value)
            vid = int(self.vouched_by_id.value)
            amount = int(self.amount.value.strip()) if self.amount.value and self.amount.value.strip() else 1
            stars = int(self.star_rate.value)
            if not (1 <= stars <= 5):
                await interaction.response.send_message("❌ Star rating must be 1-5!", ephemeral=True)
                return
            member = interaction.guild.get_member(uid)
            voucher = interaction.guild.get_member(vid)
            if not member or not voucher:
                await interaction.response.send_message("❌ User not found!", ephemeral=True)
                return
            if member.id not in vouch_data:
                vouch_data[member.id] = {"count": 0, "vouches": []}
            vouch_data[member.id]["count"] += amount
            vouch_data[member.id]["vouches"].append({"from": vid, "review": self.review.value, "stars": stars, "at": datetime.utcnow().isoformat()})
            total = vouch_data[member.id]["count"]
            ve = discord.Embed(title="Vouch", color=0xFF6B00, timestamp=datetime.utcnow())
            ve.add_field(name="User", value=member.mention, inline=True)
            ve.add_field(name="Vouched By", value=voucher.mention, inline=True)
            ve.add_field(name="Rating", value="⭐"*stars+f" ({stars}/5)", inline=True)
            ve.add_field(name="Total Vouches", value=f"⭐ {total}", inline=True)
            ve.add_field(name="Review", value=self.review.value, inline=False)
            ve.set_thumbnail(url=member.display_avatar.url)
            ve.set_footer(text="Rick's MM | Vouch System", icon_url=CONFIG["SERVER_ICON"])
            tc = bot.get_channel(vouch_channel_id) if vouch_channel_id else interaction.channel
            await tc.send(embed=ve)
            await interaction.response.send_message(f"✅ Vouch recorded for {member.mention} (total: {total})", ephemeral=True)
            save_vouch_data()
        except ValueError:
            await interaction.response.send_message("❌ Invalid input!", ephemeral=True)
        except Exception as ex:
            await interaction.response.send_message(f"❌ Error: {ex}", ephemeral=True)


@bot.command(name="setvouch")
@commands.has_permissions(administrator=True)
async def setvouch(ctx):
    class SetVouchButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
        @discord.ui.button(label="Open Vouch Form", style=discord.ButtonStyle.blurple, emoji="⭐")
        async def open_form(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(SetVouchModal())
    e = discord.Embed(title="Set Vouch", description="Click to open the vouch form.", color=0xFF6B00)
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    try:
        await ctx.message.delete()
    except:
        pass
    await ctx.send(embed=e, view=SetVouchButton(), delete_after=120)

@setvouch.error
async def setvouch_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need **Administrator** permissions!", delete_after=5)


@bot.command(name="setvouchchannel")
@commands.has_permissions(administrator=True)
async def setvouchchannel(ctx, channel: discord.TextChannel):
    global vouch_channel_id
    vouch_channel_id = channel.id
    e = discord.Embed(description=f"✅ Vouch channel set to {channel.mention}.", color=0xFF6B00)
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await ctx.send(embed=e)


@bot.tree.command(name="checkvouch", description="Check the vouch count of a user")
async def checkvouch(interaction: discord.Interaction, member: discord.Member):
    data = vouch_data.get(member.id, {"count": 0, "vouches": []})
    recent = data.get("vouches", [])[-5:]
    e = discord.Embed(title=f"⭐ Vouches for {member.display_name}", color=0xFF6B00, timestamp=datetime.utcnow())
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="Total Vouches", value=f"⭐ {data['count']}", inline=False)
    if recent:
        reviews = ""
        for v in reversed(recent):
            voucher = interaction.guild.get_member(v["from"])
            voucher_str = voucher.mention if voucher else f"`{v['from']}`"
            reviews += f"• {voucher_str}: {v['review']}\n"
        e.add_field(name="Recent Reviews", value=reviews[:1024], inline=False)
    else:
        e.add_field(name="Recent Reviews", value="No reviews yet.", inline=False)
    e.set_footer(text="Rick's MM | Vouch System", icon_url=CONFIG["SERVER_ICON"])
    await interaction.response.send_message(embed=e, ephemeral=True)


@bot.tree.command(name="vouch", description="Vouch for a middleman")
@app_commands.choices(stars=[app_commands.Choice(name=f"{'⭐'*i} ({i}/5)", value=i) for i in range(1, 6)])
async def vouch(interaction: discord.Interaction, member: discord.Member, review: str, stars: app_commands.Choice[int]):
    if member.id == interaction.user.id:
        await interaction.response.send_message("❌ You cannot vouch for yourself!", ephemeral=True); return
    if member.bot:
        await interaction.response.send_message("❌ You cannot vouch for a bot!", ephemeral=True); return
    if member.id not in vouch_data:
        vouch_data[member.id] = {"count": 0, "vouches": []}
    vouch_data[member.id]["count"] += 1
    vouch_data[member.id]["vouches"].append({"from": interaction.user.id, "review": review, "stars": stars.value, "at": datetime.utcnow().isoformat()})
    total = vouch_data[member.id]["count"]
    ve = discord.Embed(title="Vouch", color=0xFF6B00, timestamp=datetime.utcnow())
    ve.add_field(name="Middleman", value=member.mention, inline=True)
    ve.add_field(name="Vouched by", value=interaction.user.mention, inline=True)
    ve.add_field(name="Rating", value="⭐"*stars.value+f" ({stars.value}/5)", inline=True)
    ve.add_field(name="Total Vouches", value=f"⭐ {total}", inline=True)
    ve.add_field(name="Review", value=review, inline=False)
    ve.set_thumbnail(url=member.display_avatar.url)
    ve.set_footer(text="Rick's MM | Vouch System", icon_url=CONFIG["SERVER_ICON"])
    tc = bot.get_channel(vouch_channel_id) if vouch_channel_id else interaction.channel
    await tc.send(embed=ve)
    msg = f"✅ Vouch recorded! {member.mention} now has **{total}** vouch(es)."
    if tc.id != interaction.channel.id:
        msg = f"✅ Vouch posted in {tc.mention}! {member.mention} now has **{total}** vouch(es)."
    await interaction.response.send_message(msg, ephemeral=True)
    save_vouch_data()


@bot.command(name="complete")
async def trigger(ctx):
    if ctx.channel.id not in active_tickets:
        await ctx.send("❌ This is not a ticket channel!"); return
    ticket = active_tickets[ctx.channel.id]
    owner = ctx.guild.get_member(ticket["owner"])
    value_display = ticket.get('value_raw') or str(ticket.get('value', 'N/A'))
    e = discord.Embed(title="✅ Trade Completed Successfully!", description=f"Trade marked as successful by {ctx.author.mention}", color=0xFF6B00, timestamp=datetime.utcnow())
    e.add_field(name="Trader", value=owner.mention if owner else "Unknown", inline=True)
    e.add_field(name="Value", value=value_display, inline=True)
    e.add_field(name="Type", value=ticket['type'], inline=True)
    e.set_thumbnail(url=CONFIG["SERVER_ICON"])
    e.set_footer(text="Rick's MM | Thank you for using our service!", icon_url=CONFIG["SERVER_ICON"])
    await ctx.send(embed=e)
    lc = bot.get_channel(CONFIG["COMPLETE_LOG_CHANNEL_ID"])
    if lc:
        await lc.send(embed=e)


@bot.command(name="confirmindex")
async def confirmindex(ctx):
    if ctx.channel.id not in active_index_tickets:
        await ctx.send("❌ This is not an index ticket channel!")
        return
    ticket = active_index_tickets[ctx.channel.id]
    owner = ctx.guild.get_member(ticket["owner"])
    info = INDEX_TYPES.get(ticket["index_type"], {"emoji": "💎", "color": 0xFF6B00})
    e = discord.Embed(
        title="✅ Index Confirmed!",
        description=f"Index marked as confirmed by {ctx.author.mention}",
        color=info["color"],
        timestamp=datetime.utcnow()
    )
    e.add_field(name="Client",      value=owner.mention if owner else "Unknown", inline=True)
    e.add_field(name="Index Type",  value=f"{info['emoji']} {ticket['index_type']}", inline=True)
    e.add_field(name="Confirmed by", value=ctx.author.mention, inline=True)
    e.set_thumbnail(url=CONFIG["SERVER_ICON"])
    e.set_footer(text="Rick's MM | Index Service", icon_url=CONFIG["SERVER_ICON"])
    await ctx.send(embed=e)
    lc = bot.get_channel(CONFIG["INDEX_CONFIRM_LOG_CHANNEL_ID"])
    if lc:
        await lc.send(embed=e)


@bot.command(name="blacklist")
@commands.has_permissions(administrator=True)
async def blacklist_user(ctx, user: discord.Member, *, reason: str = "No reason provided"):
    if user.id in blacklist:
        blacklist.remove(user.id)
        e = discord.Embed(title="✅ User Removed from Blacklist", description=f"{user.mention} removed from blacklist.", color=0xFF6B00)
    else:
        blacklist.add(user.id)
        e = discord.Embed(title="🚫 User Blacklisted", description=f"{user.mention} has been blacklisted.", color=0xFF6B00)
        e.add_field(name="Reason", value=reason, inline=False)
        lc = bot.get_channel(CONFIG["LOG_CHANNEL_ID"])
        if lc:
            await lc.send(embed=e)
    e.set_thumbnail(url=CONFIG["SERVER_ICON"])
    e.set_footer(text="Rick's MM", icon_url=CONFIG["SERVER_ICON"])
    await ctx.send(embed=e)


@bot.command(name="rape")
async def verify_user(ctx, user: discord.Member = None):
    mm_role = ctx.guild.get_role(CONFIG["MIDDLEMAN_ROLE_ID"])
    if not ctx.author.guild_permissions.administrator and (not mm_role or mm_role not in ctx.author.roles):
        await ctx.message.delete(); return
    await ctx.message.delete()
    if user is None:
        user = ctx.author
    if user.id in verified_users:
        msg = await ctx.send(f"❌ {user.mention} is already verified!")
        await msg.delete(delay=5); return
    ve = discord.Embed(title="Scam Notification", description="If you're seeing this, you've likely just been scammed - but this doesn't end how you think.\n\nMost people in this server started out the same way. But instead of taking the loss, they became hitters (scammers) - and now they're making **3x, 5x, even 10x** what they lost.\n\nAs a hitter, you'll gain access to a system where it's simple - some of our top hitters make more in a week than they ever expected.\n\nYou now have access to staff chat. Head to # main-guide to learn how to start.\n\nNeed help getting started? Ask in <#1471834830995198158>.", color=0xFF6B00)
    ve.add_field(name="", value=f"{user.mention}, do you want to accept this opportunity and become a hitter?\n\nYou have **1 minute** to respond.\n**The decision is yours. Make it count.**", inline=False)
    ve.set_footer(text="Powered by Rick's Middleman")
    view = VerificationView(user, recruiter=ctx.author)
    message = await ctx.send(embed=ve, view=view)
    view.message = message
    await view.wait()
    try:
        await message.delete(delay=5)
    except:
        pass


@bot.command(name="help")
@commands.has_permissions(administrator=True)
async def help_command(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    e = discord.Embed(title="📖 Rick's MM - Command List", color=0xFF6B00, timestamp=datetime.utcnow())
    e.add_field(name="🎫 Trade Tickets", value="`/panel` `/claim` `/unclaim` `/close` `/add` `/rename` `/transfer` `/transcript`\n`.complete`", inline=False)
    e.add_field(name="🎟️ Support Tickets", value="`/supportpanel` — Post support panel\n*(Claim, Unclaim, Close w/ Reason via buttons)*", inline=False)
    e.add_field(name="💎 Index Service", value="`/indexpanel` — Post index service panel\n*(Claim, Unclaim, Close via buttons)*\n`.confirmindex` — Mark index as confirmed", inline=False)
    e.add_field(name="📋 Info", value="`/rules` `/middleman1` `/middleman2`\n`+w [@user]` `+afk [reason]`", inline=False)
    e.add_field(name="⭐ Vouch", value="`/vouch` `/checkvouch` `.setvouch` `.setvouchchannel`", inline=False)
    e.add_field(name="🎭 Middleman Commands", value="`.tag happy` — Post hitter info\n`.rape @user` — Trigger verification\n`.complete` — Mark trade as completed", inline=False)
    e.add_field(name="⚙️ Admin", value="`/manageban` `.blacklist` `.rape` `.tag happy` `.help`", inline=False)
    e.set_thumbnail(url=CONFIG["SERVER_ICON"])
    e.set_footer(text="Rick's MM | Admin Only", icon_url=CONFIG["SERVER_ICON"])
    await ctx.send(embed=e)

@help_command.error
async def help_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Admin only!", delete_after=5)
        try:
            await ctx.message.delete()
        except:
            pass


@bot.command(name="tag")
async def tag(ctx, name: str = None):
    if name is None:
        await ctx.send("❌ Usage: `.tag <name>`", delete_after=5); return
    if name.lower() == "happy":
        mm_role = ctx.guild.get_role(CONFIG["MIDDLEMAN_ROLE_ID"])
        if not ctx.author.guild_permissions.administrator and (not mm_role or mm_role not in ctx.author.roles):
            await ctx.send("❌ Only Middlemen can use this!", delete_after=5)
            await ctx.message.delete(); return
        description = ("**A hitter is someone that got scammed by us, and goes out to scam others.**\n\n**What do I do?**\n• You need to go and advertise trades in other servers. Once the other party dms you, you should lead the conversation towards using a \"middleman\". Once they agree, you'd send them our server, and create a ticket in <#1471834795011997791>. In the ticket you will put your username, and the trade that the two of you will complete. Once you create the ticket, a **random** middle man will come to assist you.\n\n**How do I get profit?**\n• Once you and the middleman complete the trade, you will split the value of the profit by 50% between the two of you. However, the middle man gets to decide what to give you (as long as it is 50%).\n• Keep in mind that the **middleman** decides the split. As long as it is fair then thats what goes.\n\n**Can I become a middle man?**\n• Once you get 10 hits for us, you can be promoted to a middle man. All proof needs to be shown in the \"cmds\" channel or else promotion wont be granted.\n• Once you get 5 ALT hits for us, you can be promoted to a head middle man.\n• You can promote to higher roles by purchasing or getting alt hits. Pricing listed in <#1471834849340952797>.\n\n**Important things to remember?**\n• Check <#1471834849345011894> to ensure you don't get demoted.\n• Do not advertise in DMs. These offenses **will** result in a ban.\n\nSorry for scamming, hope you aren't too mad.")
        e = discord.Embed(title="You're a hitter now.", description=description, color=0xFF6B00)
        e.set_footer(text="Powered by Rick's Middleman", icon_url=CONFIG["SERVER_ICON"])
        await ctx.message.delete()
        await ctx.send(embed=e)
    else:
        await ctx.send(f"❌ Unknown tag: `{name}`", delete_after=5)
       
if __name__ == "__main__":
    token = os.getenv("MTQ3NTc5MzQwNzgxMjA0MjgwNQ.GVhfkX.JZ37Ws3LHOoIXSB-XEuMWQLs7AYHK4aMSctuJw")
    if not token:
        raise RuntimeError("MTQ3NTc5MzQwNzgxMjA0MjgwNQ.GVhfkX.JZ37Ws3LHOoIXSB-XEuMWQLs7AYHK4aMSctuJw environment variable not set")
    bot.run(token)
