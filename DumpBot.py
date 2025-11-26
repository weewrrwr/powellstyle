import os, io, requests, discord, asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from colorama import Fore, Style, init

# ───────────────────────────────
# ⚙️ CONFIG
# ───────────────────────────────
TOKEN = "MTQ0MzE0NDkyNzA5MjQwODMzMA.Gwkj6X.zog99TEav52IvtM76AkI-nRTJ571Lv0oRKdghs"
GUILD_ID = 1416347751280545866

init(autoreset=True)
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

# ───────────────────────────────
# 🌈 CONSOLE
# ───────────────────────────────
def banner():
    os.system("cls" if os.name == "nt" else "clear")
    print(Fore.MAGENTA + Style.BRIGHT + r"""
    ╔══════════════════════════════════════════════════════╗
        💎 POWELLSTYLE | Dump Website Bot V3.5 (DM Split)
    ╚══════════════════════════════════════════════════════╝
    """ + Style.RESET_ALL)
    print(Fore.CYAN + "⚙️  Status: " + Fore.GREEN + "Running...")
    print(Fore.CYAN + "🪄  Command: " + Fore.YELLOW + "/dump <url>")
    print(Fore.CYAN + "💬  Output: " + Fore.WHITE + "Each file sent via DM\n")

def log_ok(msg): print(Fore.GREEN + "[OK] " + Fore.WHITE + msg)
def log_info(msg): print(Fore.CYAN + "[INFO] " + Fore.WHITE + msg)
def log_error(msg): print(Fore.RED + "[ERROR] " + Fore.WHITE + msg)
banner()

# ───────────────────────────────
# 🧩 Utility
# ───────────────────────────────
def safe_filename(url):
    name = os.path.basename(url.split("?")[0]) or "index.html"
    return name.replace(":", "_").replace("/", "_")

def upload_transfer(data: bytes, filename: str):
    try:
        r = requests.put(f"https://transfer.sh/{filename}", data=data)
        if r.status_code == 200:
            return r.text.strip()
    except Exception as e:
        log_error(f"Upload failed: {e}")
    return None

def get_subfolder_for_ext(ext):
    ext = ext.lower()
    if ext in [".css"]: return "css"
    if ext in [".js"]: return "js"
    if ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp"]: return "images"
    if ext in [".mp4", ".webm", ".ogg", ".mov"]: return "videos"
    if ext in [".mp3", ".wav", ".m4a"]: return "audio"
    if ext in [".woff", ".woff2", ".ttf", ".otf", ".eot"]: return "fonts"
    return "assets"

# ───────────────────────────────
# 🌐 Dump Website
# ───────────────────────────────
def dump_website(base_url):
    if not base_url.startswith("http"):
        base_url = "https://" + base_url
    parsed = urlparse(base_url)
    folder_name = parsed.netloc.replace("www.", "")
    os.makedirs(folder_name, exist_ok=True)
    try:
        html = requests.get(base_url, timeout=10).text
    except Exception as e:
        log_error(f"Cannot load website: {e}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    tags = {
        "link": ["href"], "script": ["src"], "img": ["src", "data-src"],
        "source": ["src"], "video": ["src"], "audio": ["src"],
        "iframe": ["src"], "embed": ["src"], "object": ["data"]
    }

    files = []
    total = sum(len(soup.find_all(tag)) for tag in tags.keys())
    done = 0

    for tag, attrs in tags.items():
        for el in soup.find_all(tag):
            for attr in attrs:
                link = el.get(attr)
                if not link: continue
                full = urljoin(base_url, link)
                try:
                    res = requests.get(full, timeout=10)
                    if res.status_code == 200:
                        filename = safe_filename(full)
                        sub = get_subfolder_for_ext(os.path.splitext(filename)[1])
                        dirp = os.path.join(folder_name, sub)
                        os.makedirs(dirp, exist_ok=True)
                        path = os.path.join(dirp, filename)
                        with open(path, "wb") as f: f.write(res.content)
                        files.append((path, filename))
                        done += 1
                        percent = int((done / total) * 100)
                        print(Fore.GREEN + f"  ▰ {percent:>3}% | {filename}")
                except:
                    pass

    off = os.path.join(folder_name, "index_offline.html")
    with open(off, "w", encoding="utf-8") as f: f.write(str(soup))
    files.append((off, "index_offline.html"))
    log_ok(f"Downloaded {len(files)} files")
    return files

# ───────────────────────────────
# 💬 Discord Command
# ───────────────────────────────
@tree.command(name="dump", description="Dump เว็บไซต์และส่งไฟล์ทั้งหมดให้ใน DM (Powellstyle)")
async def dump_command(interaction: discord.Interaction, url: str):
    await interaction.response.send_message(f"⚙️ กำลังโหลด `{url}` ... 💜", ephemeral=False)
    files = dump_website(url)
    if not files:
        await interaction.followup.send("❌ โหลดเว็บไม่สำเร็จ")
        return

    user = interaction.user
    dm = await user.create_dm()
    await dm.send(f"💎 **POWELLSTYLE DUMP RESULT**\n🌐 URL: `{url}`\n📂 Files: {len(files)}\n\nกำลังส่งไฟล์ทั้งหมด...")

    for path, name in files:
        try:
            size = os.path.getsize(path) / (1024 * 1024)
            if size > 25:
                with open(path, "rb") as f:
                    link = upload_transfer(f.read(), name)
                    if link:
                        await dm.send(f"📎 `{name}` ({round(size,2)} MB)\n🔗 {link}")
            else:
                await dm.send(file=discord.File(path))
        except Exception as e:
            await dm.send(f"⚠️ `{name}` ส่งไม่สำเร็จ ({e})")

    await dm.send("✅ เสร็จสิ้น! 💜 ส่งไฟล์ทั้งหมดให้แล้ว")
    await interaction.followup.send("📩 ส่งไฟล์ทั้งหมดให้ใน DM แล้ว ✅")

# ───────────────────────────────
# 🚀 Boot
# ───────────────────────────────
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    banner()
    log_ok(f"Logged in as {bot.user}")
    while True:
        await asyncio.sleep(1)

bot.run(TOKEN)
