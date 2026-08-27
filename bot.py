import discord
from discord.ext import commands
import json
import os
from datetime import datetime, timezone
from aiohttp import web
import asyncio

# --- ВЕБСЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- ФАЙЛОВІ ОПЕРАЦІЇ ---
def load_data(file, default):
    if not os.path.exists(file):
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(default, f, ensure_ascii=False, indent=4)
    with open(file, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return default

def save_data(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)

# ID ролей та каналів
КАНАЛ_ПРИВІТАНЬ = 1369618429836923010  
РОЛЬ_УРЯДОВЕЦЬ = 1369616562134188082  
РОЛЬ_КОНСУЛ = 1369616488025296948   
РОЛЬ_ЗА_МЕШКАНЕЦЬ = 1369616831874207857  
РОЛЬ_ЗА_ГІСТЬ = 1369616891445776435  

ROLE_PRIBYLYI = 1422263731597082675
ROLE_OSELENETS = 1422264026607390801
ROLE_SHUKACH = 1422264170002255893
ROLE_ZHYTEL = 1422264257562808411
ROLE_MAYSTER = 1458554868099846368
ROLE_KHRANYTEL = 1458555026804048104
ROLE_VARTOVYI = 1458555174640681094
ROLE_LEGENDA = 1458555330656080116
ROLE_LORD = 1458555480124424253

КАНАЛ_ЛОГІВ = 1458559571370053696  
КАНАЛ_ЛІДЕРБОРДУ = 1542471245302341692 

RANK_ROLES = {
    "👣 Прибулий": ROLE_PRIBYLYI,
    "🏠 Оселенець": ROLE_OSELENETS,
    "🔎 Шукач": ROLE_SHUKACH,
    "🏘️ Житель": ROLE_ZHYTEL,
    "🔨 Майстер": ROLE_MAYSTER,
    "💠 Хранитель": ROLE_KHRANYTEL,
    "🛡️ Вартовий": ROLE_VARTOVYI,
    "🎖️ Легенда Містенції": ROLE_LEGENDA,
    "👑 Лорд Містенції": ROLE_LORD
}

BALANCE_FILE = 'balance.json'
TIMESTAMPS_FILE = 'timestamps.json' 
LEDBEAR_CONFIG = 'leaderboard_msg.json'
NICKNAMES_FILE = 'nicknames.json'

def load_balance(): return load_data(BALANCE_FILE, {})
def save_balance(balance): save_data(BALANCE_FILE, balance)
def load_timestamps(): return load_data(TIMESTAMPS_FILE, {})
def save_timestamps(data): save_data(TIMESTAMPS_FILE, data)
def load_nicknames(): return load_data(NICKNAMES_FILE, {})
def save_nicknames(data): save_data(NICKNAMES_FILE, data)

def get_game_name(user_id, default_name):
    nicknames = load_nicknames()
    return nicknames.get(str(user_id), default_name)

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущено!')
    bot.add_view(WelcomeButtons())  
    bot.add_view(HelpButtons())     
    
    try:
        await bot.tree.sync()
        print("✅ Усі слеш-команди успішно синхронізовано!")
    except Exception as e:
        print(f"Помилка синхронізації команд: {e}")
        
    await update_persistent_leaderboard()

# --- ЛІДЕРБОРД ---
async def update_persistent_leaderboard():
    if КАНАЛ_ЛІДЕРБОРДУ == 0: return
    channel = bot.get_channel(КАНАЛ_ЛІДЕРБОРДУ)
    if not channel: return

    balance = load_balance()
    embed = discord.Embed(title="🏆 Топ мешканців Містенції", description="Рейтинг гравців за ігровими ніками та їхні поточні ранги", color=0x9B59B6)

    if not balance:
        embed.add_field(name="Рейтинг:", value="❌ Лідерборд поки що порожній.", inline=False)
    else:
        sorted_users = sorted(balance.items(), key=lambda x: x[1], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        leaderboard_text = ""

        for index, (user_id, points) in enumerate(sorted_users[:20]):
            member = channel.guild.get_member(int(user_id))
            fallback_name = member.display_name if member else f"Мандрівник ({user_id})"
            game_name = get_game_name(user_id, fallback_name)
            
            place_str = medals[index] if index < 3 else f"`#{index + 1}`"
            rank = get_rank_name(points)
            leaderboard_text += f"{place_str} **{game_name}** — {points} балів\n╰ *{rank}*\n\n"

        embed.add_field(name="Рейтинг:", value=leaderboard_text, inline=False)
    
    embed.set_footer(text="Оновлюється автоматично • Містенція")
    data = load_data(LEDBEAR_CONFIG, {"msg_id": None})
    msg_id = data.get("msg_id")

    try:
        if msg_id:
            msg = await channel.fetch_message(msg_id)
            await msg.edit(embed=embed)
        else:
            raise Exception()
    except:
        new_msg = await channel.send(embed=embed)
        save_data(LEDBEAR_CONFIG, {"msg_id": new_msg.id})

@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(КАНАЛ_ПРИВІТАНЬ)
    if channel:
        await channel.send(
            f"👋 Вітаємо {member.mention} на сервері Містенція!\n"
            f"Будь ласка, зачекайте, поки уряд видасть вам роль.\n\n"
            f"Урядовці, натисніть кнопку нижче:",
            view=WelcomeButtons(member.id)
        )

class WelcomeButtons(discord.ui.View):
    def __init__(self, user_id=None):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="💜 Мешканець", style=discord.ButtonStyle.success, custom_id="welcome_accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.user.roles, id=РОЛЬ_УРЯДОВЕЦЬ):
            try:
                member = await interaction.guild.fetch_member(self.user_id)
                await member.add_roles(discord.Object(id=РОЛЬ_ЗА_МЕШКАНЕЦЬ))
                
                try:
                    await member.send("💜 Вітаємо у Містенції! Напиши у відповідь на це повідомлення свій **ігровий нік** для лідерборда:")
                    msg = await bot.wait_for('message', timeout=180.0, check=lambda m: m.author.id == member.id and isinstance(m.channel, discord.DMChannel))
                    nicknames = load_nicknames()
                    nicknames[str(member.id)] = msg.content.strip()
                    save_nicknames(nicknames)
                    await member.send(f"✅ Збережено ігровий нік: **{msg.content.strip()}**")
                    await update_persistent_leaderboard()
                except:
                    pass
                
                await interaction.response.send_message(f"{member.mention} прийнятий як Мешканець! ✅", ephemeral=True)
            except:
                await interaction.response.send_message("❌ Не вдалося знайти користувача.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Немає прав Урядовця!", ephemeral=True)

    @discord.ui.button(label="❌ Гість", style=discord.ButtonStyle.danger, custom_id="welcome_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.user.roles, id=РОЛЬ_УРЯДОВЕЦЬ):
            try:
                member = await interaction.guild.fetch_member(self.user_id)
                await member.add_roles(discord.Object(id=РОЛЬ_ЗА_ГІСТЬ))
                await interaction.response.send_message(f"{member.mention} тепер Гість. ❌", ephemeral=True)
            except:
                await interaction.response.send_message("❌ Помилка.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Немає прав Урядовця!", ephemeral=True)

class HelpButtons(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🌍 Гайд по Долині", style=discord.ButtonStyle.primary, custom_id="help_guide")
    async def guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = (
            "👋 **Вітаю тебе на Долині!** Розкажу тобі основу, щоб ти міг увійти:\n\n"
            "💰 **Валюта:**\n• **НЗ** — необроблене золото\n• **БНЗ** — блоки необробленого золота\n\n"
            "🏛️ **Державний устрій:**\nГолова країни — **Президент**. Закони приймає **Парламент**.\n"
        )
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="🏛️ Про Містенцію", style=discord.ButtonStyle.secondary, custom_id="help_mystencia")
    async def about(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("💜 **Вітаю тебе в Містенції!** Тут твоя безпека та комфорт.", ephemeral=True)

@bot.tree.command(name="довідка", description="Отримати довідку по серверу")
async def send_help(interaction: discord.Interaction):
    embed = discord.Embed(title="📚 Довідка Містенції", description="Вітаю в довідці! Натискай кнопку нижче.", color=0x9B59B6)
    await interaction.response.send_message(embed=embed, view=HelpButtons(), ephemeral=True)

def get_rank_name(points):
    if points <= 10: return "👣 Прибулий"
    elif points <= 20: return "🏠 Оселенець"
    elif points <= 30: return "🔎 Шукач"
    elif points <= 50: return "🏘️ Житель"
    elif points <= 75: return "🔨 Майстер"
    elif points <= 100: return "💠 Хранитель"
    elif points <= 130: return "🛡️ Вартовий"
    elif points <= 150: return "🎖️ Легенда Містенції"
    else: return "👑 Лорд Містенції"

# --- ВИДАЛЕННЯ МЕШКАНЦЯ ---
class ConfirmDeleteView(discord.ui.View):
    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=60)
        self.target_member = target_member

    @discord.ui.button(label="Підтвердити видалення", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = str(self.target_member.id)
        for file, data in [(BALANCE_FILE, load_balance()), (TIMESTAMPS_FILE, load_timestamps()), (NICKNAMES_FILE, load_nicknames())]:
            if uid in data:
                del data[uid]
                save_data(file, data)

        await update_persistent_leaderboard()
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content=f"✅ Користувача {self.target_member.mention} повністю стерто з усіх баз.", view=self)
        self.stop()

    @discord.ui.button(label="Скасувати", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content="❌ Видалення скасовано.", view=self)
        self.stop()

@bot.tree.command(name="видалити_мешканця", description="Повністю стерти дані мешканця з усіх файлів (тільки Консул)")
async def delete_resident(interaction: discord.Interaction, member: discord.Member):
    if not discord.utils.get(interaction.user.roles, id=РОЛЬ_КОНСУЛ):
        await interaction.response.send_message("❌ Цю команду може виконувати лише Консул!", ephemeral=True)
        return
    view = ConfirmDeleteView(member)
    embed = discord.Embed(
        title="⚠️ Підтвердження повного видалення",
        description=f"Ви збираєтесь **повністю стерти** всі дані користувача {member.mention}.\n\nЦю дію неможливо скасувати. Продовжити?",
        color=0xE74C3C
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# --- ОПИТУВАННЯ НІКІВ ---
@bot.tree.command(name="опитування_ніків", description="Запитати ігровий нік у мешканців без ніка (тільки Уряд)")
async def ask_all_nicknames(interaction: discord.Interaction):
    if not discord.utils.get(interaction.user.roles, id=РОЛЬ_УРЯДОВЕЦЬ):
        await interaction.response.send_message("❌ У вас немає прав Урядовця!", ephemeral=True)
        return

    await interaction.response.send_message("🔄 Розпочато розсилку запитів на ігрові ніки в ЛС...", ephemeral=True)
    nicknames = load_nicknames()
    role = interaction.guild.get_role(РОЛЬ_ЗА_МЕШКАНЕЦЬ)
    count = 0

    if role:
        for member in role.members:
            if str(member.id) not in nicknames:
                try:
                    await member.send("💜 Напиши свій **ігровий нік** для лідерборда та паспорта:")
                    msg = await bot.wait_for('message', timeout=60.0, check=lambda m: m.author.id == member.id and isinstance(m.channel, discord.DMChannel))
                    nicknames[str(member.id)] = msg.content.strip()
                    save_nicknames(nicknames)
                    count += 1
                except:
                    pass

    await update_persistent_leaderboard()
    await interaction.followup.send(f"✅ Опитування завершено! Зібрано ніків для {count} мешканців.", ephemeral=True)

# --- БАЛИ ПЛЮС (З DEFER ДЛЯ ЗАХИСТУ ВІД ТАЙМ-АУТУ) ---
@bot.tree.command(name="бали_плюс", description="Додати бали кільком мешканцям одразу")
async def add_points(interaction: discord.Interaction, members_input: str, points: int, reason: str = "Причина не вказана"):
    await interaction.response.defer(ephemeral=True)

    if not discord.utils.get(interaction.user.roles, id=РОЛЬ_УРЯДОВЕЦЬ):
        await interaction.followup.send("❌ У вас немає прав Урядовця!", ephemeral=True)
        return

    balance, timestamps, success = load_balance(), load_timestamps(), []
    current_time = datetime.now(timezone.utc).isoformat()

    for part in members_input.strip().split():
        clean_id = part.replace("<@", "").replace(">", "").replace("!", "")
        if clean_id.isdigit():
            member = interaction.guild.get_member(int(clean_id))
            if member:
                uid = str(member.id)
                balance[uid] = balance.get(uid, 0) + points
                timestamps[uid] = current_time
                await update_member_rank_role(member, balance[uid])
                success.append(member.mention)

    if not success:
        await interaction.followup.send("❌ Не вдалося знайти жодного мешканця!", ephemeral=True)
        return

    save_balance(balance)
    save_timestamps(timestamps)
    await update_persistent_leaderboard()

    mentions_str = ", ".join(success)
    embed_user = discord.Embed(description=f"✅ Нараховано **+{points} балів** для: {mentions_str}!\n📜 **За:** {reason}", color=0x9B59B6)
    
    await interaction.channel.send(embed=embed_user)
    await interaction.followup.send("✅ Команда успішно виконана!", ephemeral=True)

    try:
        log_channel = bot.get_channel(КАНАЛ_ЛОГІВ)
        if log_channel:
            embed_log = discord.Embed(title="📜 Офіційний звіт: Нарахування", color=0x9B59B6, timestamp=interaction.created_at)
            embed_log.add_field(name="✍️ Урядовець:", value=interaction.user.mention, inline=True)
            embed_log.add_field(name="👥 Отримувачі:", value=mentions_str, inline=False)
            embed_log.add_field(name="💰 Кількість:", value=f"**+{points}** балів", inline=True)
            embed_log.add_field(name="📝 Коментар:", value=f"*{reason}*", inline=False)
            await log_channel.send(embed=embed_log)
    except Exception as e:
        print(f"Помилка логів: {e}")

# --- БАЛИ МІНУС (З DEFER ДЛЯ ЗАХИСТУ ВІД ТАЙМ-АУТУ) ---
@bot.tree.command(name="бали_мінус", description="Зняти бали (штраф) у кількох мешканців одразу")
async def remove_points(interaction: discord.Interaction, members_input: str, points: int, reason: str = "Причина не вказана"):
    await interaction.response.defer(ephemeral=True)

    if not discord.utils.get(interaction.user.roles, id=РОЛЬ_УРЯДОВЕЦЬ):
        await interaction.followup.send("❌ У вас немає прав Урядовця!", ephemeral=True)
        return

    balance, timestamps, success = load_balance(), load_timestamps(), []
    current_time = datetime.now(timezone.utc).isoformat()

    for part in members_input.strip().split():
        clean_id = part.replace("<@", "").replace(">", "").replace("!", "")
        if clean_id.isdigit():
            member = interaction.guild.get_member(int(clean_id))
            if member:
                uid = str(member.id)
                balance[uid] = max(balance.get(uid, 0) - points, 0)
                timestamps[uid] = current_time
                await update_member_rank_role(member, balance[uid])
                success.append(member.mention)

    if not success:
        await interaction.followup.send("❌ Не вдалося знайти жодного мешканця!", ephemeral=True)
        return

    save_balance(balance)
    save_timestamps(timestamps)
    await update_persistent_leaderboard()

    mentions_str = ", ".join(success)
    embed_user = discord.Embed(description=f"⚠️ Знято **-{points} балів** у: {mentions_str}.\n📜 **Причина:** {reason}", color=0xE74C3C)
    
    await interaction.channel.send(embed=embed_user)
    await interaction.followup.send("✅ Команда успішно виконана!", ephemeral=True)

    try:
        log_channel = bot.get_channel(КАНАЛ_ЛОГІВ)
        if log_channel:
            embed_log = discord.Embed(title="⚖️ Офіційний звіт: Штраф", color=0xE74C3C, timestamp=interaction.created_at)
            embed_log.add_field(name="✍️ Хто виписав:", value=interaction.user.mention, inline=True)
            embed_log.add_field(name="👥 Порушники:", value=mentions_str, inline=False)
            embed_log.add_field(name="💰 Штраф:", value=f"-{points} балів", inline=True)
            embed_log.add_field(name="📝 Причина:", value=f"*{reason}*", inline=False)
            await log_channel.send(embed=embed_log)
    except Exception as e:
        print(f"Помилка логів: {e}")

# --- ПАСПОРТ ГРАВЦЯ ---
@bot.tree.command(name="бали", description="Переглянути свій паспорт та час останніх балів")
async def check_points(interaction: discord.Interaction, member: discord.Member = None):
    balance, timestamps = load_balance(), load_timestamps()
    target = member or interaction.user
    uid = str(target.id)
    pts = balance.get(uid, 0)
    
    rank = get_rank_name(pts)
    game_name = get_game_name(uid, target.display_name)
    
    thresholds = [0, 10, 20, 30, 50, 75, 100, 130, 150, 200]
    next_goal = 200
    for t in thresholds:
        if t > pts:
            next_goal = t
            break
            
    progress = min(int((pts / next_goal) * 10), 10) if next_goal > 0 else 10
    bar = "▰" * progress + "▱" * (10 - progress)
    percent = int((pts / next_goal) * 100) if next_goal > 0 else 100

    guild_member = interaction.guild.get_member(target.id)
    joined_at = guild_member.joined_at.strftime("%d.%m.%Y") if guild_member and guild_member.joined_at else "Невідомо"

    last_time_str = timestamps.get(uid)
    if last_time_str:
        diff = datetime.now(timezone.utc) - datetime.fromisoformat(last_time_str)
        hours = int(diff.total_seconds() // 3600)
        days = hours // 24
        time_ago = f"{days} дн. тому" if days > 0 else (f"{hours} год. тому" if hours > 0 else "щойно")
    else:
        time_ago = "Ще не отримував(-ла)"

    emb = discord.Embed(title=f"💳 Офіційний паспорт: {game_name}", color=0x9B59B6)
    emb.set_thumbnail(url=target.display_avatar.url)
    emb.add_field(name="👤 Мешканець", value=target.mention, inline=True)
    emb.add_field(name="🎮 Ігровий нік", value=game_name, inline=True)
    emb.add_field(name="📅 У місті з:", value=joined_at, inline=True)
    emb.add_field(name="💰 Поточний баланс", value=f"**{pts}** балів", inline=True)
    emb.add_field(name="🎖️ Ранг", value=rank, inline=True)
    emb.add_field(name=f"📊 Прогрес до цілі ({next_goal} балів)", value=f"**{bar}** {percent}%\n*Залишилось: {max(0, next_goal - pts)} балів*", inline=False)
    emb.add_field(name="⏳ Останні бали", value=f"*{time_ago}*", inline=False)
    emb.set_footer(text="Містенція • Державна автоматизація", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    await interaction.response.send_message(embed=emb, ephemeral=True)

async def update_member_rank_role(member, points):
    current_rank_name = get_rank_name(points)
    target_role_id = RANK_ROLES.get(current_rank_name)
    if not target_role_id: return

    try:
        for role_id in RANK_ROLES.values():
            role = member.guild.get_role(role_id)
            if role and role in member.roles and role_id != target_role_id:
                await member.remove_roles(role)
        
        new_role = member.guild.get_role(target_role_id)
        if new_role and new_role not in member.roles:
            await member.add_roles(new_role)
    except Exception as e:
        print(f"Помилка при зміні ролі: {e}")

async def main():
    await start_web_server()
    await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
