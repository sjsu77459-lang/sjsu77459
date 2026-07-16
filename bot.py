import asyncio, os, random, json
from collections import defaultdict
from datetime import datetime, timedelta
import yt_dlp
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ChatMemberStatus

TOKEN = "8717101139:AAFlXPGgVOPZOkyQTbvVBAwkPMYBJ7Il5BQ"
OWNER_ID = 8717101139
CHANNELS = ["@kozmetikfornour25", "@lIl0o0ll"]
DATA_FILE = "bella_data.json"

v = set()
warnings_dict = defaultdict(lambda: {"c":0, "mutes":0})
points = defaultdict(int)
spam_data = defaultdict(lambda: {"m":[], "l":datetime.now()})
sub_reminder = {}
active_games = {}
million_games = {}
settings = {"mus":True, "dl":True, "dg_edit":True, "ds":True, "dm":True, "as":True, "fs":True, "bw":True}
BAD_WORDS = ["كس","طيز","عير","زب","منيوك","شرموط","قحبه","ديوث","داعش","قاعدة","جهادي","ارهابي"]
RANKS = {1:"جندي",2:"جندي أول",3:"رقيب",4:"رقيب أول",5:"ملازم",6:"ملازم أول",7:"نقيب",8:"رائد",9:"مقدم",10:"عقيد",11:"عميد",12:"لواء",13:"فريق",14:"فريق أول",15:"مشير",16:"ركن",17:"ملك"}
user_ranks = defaultdict(int)

def get_rank(pts):
    if pts >= 3000: return "ملك"
    if pts >= 2000: return "ركن"
    for th, rank in sorted(RANKS.items(), reverse=True):
        if th <= 15 and pts >= th*100: return rank
    return "جندي"

def is_high_rank(uid, pts=None):
    if uid == OWNER_ID: return True
    if pts is None: pts = points[uid]
    if user_ranks[uid] >= 16: return True
    return get_rank(pts) in ["مشير","ركن","ملك"]

def load():
    global v, points, warnings_dict, settings, user_ranks
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            v=set(d.get("v",[])); points.update(d.get("p",{})); warnings_dict.update(d.get("w",{})); settings.update(d.get("st",{})); user_ranks.update(d.get("ur",{}))
    except: pass
def save():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"v":list(v),"p":dict(points),"w":dict(warnings_dict),"st":settings,"ur":dict(user_ranks)}, f, ensure_ascii=False, indent=2)
load()

WEL = "🇺🇸 𓆩 𝐁𝐄𝐋𝐋𝐀 𓆪\n🛡️ بوت حماية وإدارة\n⭐ Bella Protection"
SUB = "📢 اشترك:\n@kozmetikfornour25\n@lIl0o0ll\n✅ اضغط تحقق"
HELP_MSG = """🛡️ **أوامر بيلا** 🇺🇸
🎵 `يوت + اسم` - تحميل اغنية
💰 `/rank` - رتبتك ونقاطك
👮 `/warn` (رد) - تحذير
👮 `/mute` (رد) - كتم ساعة (ملازم+)
👮 `/kick` (رد) - طرد (رائد+)
👮 `/ban` (رد) - حظر (عميد+)
🎮 **ألعاب فردية:** `/roulette` `/spy` `/bridge` `/shoot` `/airstrike` `/sniper` `/duel` `/intel`
🎮 **ألعاب جماعية:** `/survive` `/grouproulette`
🎮 **من سيربح المليون:** `/million`
⚙️ `/settings` - لوحة التحكم
🏅 `/promote` `/demote` `/setrank` (للمالك)"""

def skb(): return InlineKeyboardMarkup([[InlineKeyboardButton("🔹 @kozmetikfornour25", url="https://t.me/kozmetikfornour25")],[InlineKeyboardButton("🔹 @lIl0o0ll", url="https://t.me/lIl0o0ll")],[InlineKeyboardButton("✅ تحقق", callback_data="check")]])
def main_kb(): return InlineKeyboardMarkup([[InlineKeyboardButton("📖 الأوامر", callback_data="help")],[InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")],[InlineKeyboardButton("📊 إحصائيات", callback_data="stats")],[InlineKeyboardButton("🏅 شرح الرتب", callback_data="ranks_info")],[InlineKeyboardButton("🎮 شرح الألعاب", callback_data="games_info")]])
def settings_kb(): return InlineKeyboardMarkup([[InlineKeyboardButton(f"🎵 موسيقى: {'✅' if settings['mus'] else '❌'}", callback_data="tg_mus")],[InlineKeyboardButton(f"🔗 منع تعديل الروابط: {'✅' if settings['dl'] else '❌'}", callback_data="tg_dl")],[InlineKeyboardButton(f"🎭 منع تعديل GIF: {'✅' if settings['dg_edit'] else '❌'}", callback_data="tg_dg_edit")],[InlineKeyboardButton(f"🎯 فلتر الملصقات: {'✅' if settings['ds'] else '❌'}", callback_data="tg_ds")],[InlineKeyboardButton(f"🖼️ حذف الوسائط: {'✅' if settings['dm'] else '❌'}", callback_data="tg_dm")],[InlineKeyboardButton(f"🚫 السبام: {'✅' if settings['as'] else '❌'}", callback_data="tg_as")],[InlineKeyboardButton(f"🔒 اشتراك إجباري: {'✅' if settings['fs'] else '❌'}", callback_data="tg_fs")],[InlineKeyboardButton(f"🚷 كلمات ممنوعة: {'✅' if settings['bw'] else '❌'}", callback_data="tg_bw")],[InlineKeyboardButton("🔙 رجوع", callback_data="back")]])

def rp(t):
    t = t.lower()
    if "بوت" in t: return random.choice(["اني مو بوت، اني بيلا 🇺🇸🦅","شبيك تحسبني آلة؟ أنا بيلا!","لا تقول بوت، قول بيلا! ⚡"])
    if any(k in t for k in ["هلو","هاي","مرحبا"]): return random.choice(["شكو حياتي؟ 🦅","هلا بالبطل! منور!","نورت المجموعة! ✨","أهلاً وسهلاً! شلونك؟ 💚"])
    if "شكرا" in t: return random.choice(["العفو! 😊","تدلل!","ولا يهمك! ❤️","حاضرين للطيبين!"])
    if "شلونك" in t: return random.choice(["تمام! شلونك انت؟ 🥰","الحمد لله بخير!","كلشي تمام! 💪"])
    if "حلو" in t: return random.choice(["شفت شي مثلي؟ 😘","حلو؟ هذا الكلام يوصفني!"])
    if "غبي" in t: return random.choice(["تعال خاص هون اني الآمر 💪","مو غبي، أنا ذكي جداً!"])
    if "احبك" in t: return random.choice(["وأنا أكثر! 😍","حبيبي والله! 💕"])
    if "باي" in t: return random.choice(["مع السلامة! 👋","بااي! ترجع بالسلامة!"])
    if "صباح" in t or "مساء" in t: return random.choice(["صباح/مساء النور! ☀️","صباح/مساء الورد! 🌸"])
    return random.choice(["🇺🇸 حاضر يا بطل!","🛡️ في الخدمة!","⚡ جاهز!","🎖️ أمرك مطاع!","💂‍♂️ في حراسة الوطن!"])

async def check_sub(uid, bot):
    if uid == OWNER_ID or uid in v: return True
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(chat_id=ch, user_id=uid)
            if m.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]: return False
        except: return False
    v.add(uid); save(); return True

async def start(upd,ctx):
    if upd.effective_chat.type in ["group","supergroup"]: await upd.message.reply_text(WEL); return
    if not await check_sub(upd.effective_user.id, ctx.bot): await upd.message.reply_text(SUB, reply_markup=skb())
    else: await upd.message.reply_text(f"{WEL}\n\n{HELP_MSG}", reply_markup=main_kb())

async def help_cmd(upd,ctx): await upd.message.reply_text(HELP_MSG)
async def rank_cmd(upd,ctx): pts=points[upd.effective_user.id]; await upd.message.reply_text(f"🏅 رتبتك: {get_rank(pts)}\n💰 نقاطك: {pts}")
async def stats_cmd(upd,ctx): await upd.message.reply_text(f"📊 الأعضاء المشتركون: {len(v)}")
async def settings_cmd(upd,ctx):
    if upd.effective_user.id != OWNER_ID: return
    await upd.message.reply_text("⚙️ إعدادات الحماية", reply_markup=settings_kb())

async def add_warning(update, context, uid, chat_id, reason):
    data = warnings_dict[chat_id][uid]; data["c"] += 1
    if data["c"] >= 3:
        until = datetime.utcnow() + timedelta(minutes=10)
        await context.bot.restrict_chat_member(chat_id, uid, ChatPermissions(can_send_messages=False), until_date=until)
        await context.bot.send_message(chat_id, f"🚫 تم كتم العضو [{uid}] 10 دقائق بسبب {reason}")
        data["c"] = 0; data["mutes"] += 1
        if data["mutes"] >= 3:
            try: await context.bot.ban_chat_member(chat_id, uid); await context.bot.unban_chat_member(chat_id, uid); await context.bot.send_message(chat_id, f"🚷 تم طرد العضو [{uid}] بعد 3 كتمات"); data["mutes"]=0
            except: pass
    else: await context.bot.send_message(chat_id, f"⚠️ تحذير {data['c']}/3 للعضو [{uid}] بسبب {reason}")
    save()

async def warn_cmd(upd,ctx):
    if upd.effective_user.id != OWNER_ID or not upd.message.reply_to_message: return
    await add_warning(upd, ctx, upd.message.reply_to_message.from_user.id, upd.effective_chat.id, "إداري")

async def mute_cmd(upd,ctx):
    if not upd.message.reply_to_message: return
    uid = upd.effective_user.id; target = upd.message.reply_to_message.from_user.id
    if uid != OWNER_ID and not is_high_rank(uid) and get_rank(points[uid]) not in ["ملازم","ملازم أول","نقيب","رائد","مقدم","عقيد","عميد","لواء","فريق","فريق أول","مشير","ركن","ملك"]:
        await upd.message.reply_text("❌ رتبتك لا تسمح بالكتم."); return
    try: await ctx.bot.restrict_chat_member(upd.effective_chat.id, target, ChatPermissions(can_send_messages=False), until_date=datetime.now()+timedelta(hours=1)); await upd.message.reply_text("🔇 تم الكتم ساعة")
    except: pass

async def kick_cmd(upd,ctx):
    if not upd.message.reply_to_message: return
    uid = upd.effective_user.id; target = upd.message.reply_to_message.from_user.id
    if uid != OWNER_ID and not is_high_rank(uid) and get_rank(points[uid]) not in ["رائد","مقدم","عقيد","عميد","لواء","فريق","فريق أول","مشير","ركن","ملك"]:
        await upd.message.reply_text("❌ رتبتك لا تسمح بالطرد."); return
    try: await ctx.bot.ban_chat_member(upd.effective_chat.id, target); await ctx.bot.unban_chat_member(upd.effective_chat.id, target); await upd.message.reply_text("👢 تم الطرد")
    except: pass

async def ban_cmd(upd,ctx):
    if not upd.message.reply_to_message: return
    uid = upd.effective_user.id; target = upd.message.reply_to_message.from_user.id
    if uid != OWNER_ID and not is_high_rank(uid) and get_rank(points[uid]) not in ["عميد","لواء","فريق","فريق أول","مشير","ركن","ملك"]:
        await upd.message.reply_text("❌ رتبتك لا تسمح بالحظر."); return
    try: await ctx.bot.ban_chat_member(upd.effective_chat.id, target); await upd.message.reply_text("🚫 تم الحظر")
    except: pass

async def promote(upd,ctx):
    if upd.effective_user.id != OWNER_ID or not upd.message.reply_to_message: return
    uid = upd.message.reply_to_message.from_user.id; user_ranks[uid] = min(17, user_ranks.get(uid, 0)+1); save(); await upd.message.reply_text(f"✅ تم ترقية العضو إلى {RANKS.get(user_ranks[uid], 'ملك')}")

async def demote(upd,ctx):
    if upd.effective_user.id != OWNER_ID or not upd.message.reply_to_message: return
    uid = upd.message.reply_to_message.from_user.id
    if user_ranks.get(uid,0)>0: user_ranks[uid]-=1; save(); await upd.message.reply_text(f"✅ تم خفض رتبة العضو إلى {RANKS.get(user_ranks[uid], 'جندي')}")
    else: await upd.message.reply_text("العضو لا يملك رتبة مخصصة.")

async def setrank(upd,ctx):
    if upd.effective_user.id != OWNER_ID or not upd.message.reply_to_message: return
    try: new_rank = int(ctx.args[0]); 
    if new_rank<1 or new_rank>17: raise ValueError
    uid = upd.message.reply_to_message.from_user.id; user_ranks[uid] = new_rank; save(); await upd.message.reply_text(f"✅ تم تعيين رتبة {RANKS.get(new_rank, '')}")
    except: await upd.message.reply_text("استخدام: /setrank <رقم من 1-17> بالرد على العضو")

async def btn(upd,ctx):
    q = upd.callback_query; await q.answer(); uid = q.from_user.id; d = q.data
    if d == "check":
        if await check_sub(uid, ctx.bot): v.add(uid); save(); await q.edit_message_text(f"✅ تم التحقق!\n\n{HELP_MSG}", reply_markup=main_kb())
        else: await q.edit_message_text(SUB, reply_markup=skb())
    elif d == "settings":
        if uid != OWNER_ID: await q.answer("للمالك فقط", show_alert=True); return
        await q.edit_message_text("⚙️ إعدادات الحماية", reply_markup=settings_kb())
    elif d == "help": await q.edit_message_text(HELP_MSG, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]))
    elif d == "stats": await q.edit_message_text(f"📊 الأعضاء: {len(v)}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]))
    elif d == "ranks_info":
        txt = "🏅 الرتب:\n" + "\n".join([f"{th}. {rank} ({th*100 if th<=15 else '2000+' if th==16 else '3000+'} نقطة)" for th, rank in RANKS.items()])
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]))
    elif d == "games_info":
        txt = "🎮 الألعاب الفردية: /roulette, /spy, /bridge, /shoot, /airstrike, /sniper, /duel, /intel\n🎮 الألعاب الجماعية: /survive, /grouproulette\n🎮 من سيربح المليون: /million"
        await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]))
    elif d == "back": await q.edit_message_text(f"{WEL}\n\n{HELP_MSG}", reply_markup=main_kb())
    elif uid == OWNER_ID and d.startswith("tg_"): key = d[3:]; settings[key] = not settings[key]; save(); await q.edit_message_text("⚙️", reply_markup=settings_kb())

# ========== الألعاب ==========
async def roulette(upd,ctx):
    try: bet = int(ctx.args[0]); uid = upd.effective_user.id
    if points[uid] < bet and not is_high_rank(uid): return await upd.message.reply_text("نقاطك ما تكفي")
    if random.randint(1,6)==1:
        if not is_high_rank(uid): points[uid] -= bet
        await upd.message.reply_text(f"💥 خسرت {bet}. رصيدك {points[uid] if not is_high_rank(uid) else 'لا نهائي'}")
    else: win = bet*2; 
    if not is_high_rank(uid): points[uid] += win
    await upd.message.reply_text(f"🎯 ربحت {win}. رصيدك {points[uid] if not is_high_rank(uid) else 'لا نهائي'}")
    save()
    except: await upd.message.reply_text("/roulette <نقاط>")

async def spy(upd,ctx):
    uid=upd.effective_user.id
    if random.random()<0.5:
        if not is_high_rank(uid): points[uid]+=30
        await upd.message.reply_text(f"🕵️ +30. رصيدك {points[uid]}")
    else:
        if not is_high_rank(uid): points[uid]=max(0,points[uid]-20)
        await upd.message.reply_text(f"🕵️ -20. رصيدك {points[uid]}")
    save()
async def bridge(upd,ctx):
    uid=upd.effective_user.id
    if random.random()<0.3:
        if not is_high_rank(uid): points[uid]=max(0,points[uid]-50)
        await upd.message.reply_text(f"💣 -50. رصيدك {points[uid]}")
    else: await upd.message.reply_text("💣 نجوت!")
    save()
async def shoot(upd,ctx):
    uid=upd.effective_user.id
    if random.random()<0.7:
        if not is_high_rank(uid): points[uid]+=10
        await upd.message.reply_text(f"🎯 +10. رصيدك {points[uid]}")
    else: await upd.message.reply_text("🎯 أخطأت!")
    save()
async def airstrike(upd,ctx):
    uid=upd.effective_user.id
    if random.random()<0.4:
        if not is_high_rank(uid): points[uid]+=30
        await upd.message.reply_text(f"🚁 +30. رصيدك {points[uid]}")
    else: await upd.message.reply_text("🚁 فشل!")
    save()
async def sniper(upd,ctx):
    uid=upd.effective_user.id
    if random.random()<0.2:
        if not is_high_rank(uid): points[uid]+=50
        await upd.message.reply_text(f"🏆 +50. رصيدك {points[uid]}")
    else: await upd.message.reply_text("🏆 أخطأت!")
    save()
async def duel(upd,ctx):
    if not upd.message.reply_to_message: return await upd.message.reply_text("⚔️ استخدم بالرد على خصمك")
    u1=upd.effective_user.id; u2=upd.message.reply_to_message.from_user.id
    if u1==u2: return await upd.message.reply_text("لا تبارز نفسك!")
    if points[u1]<40 and not is_high_rank(u1): return await upd.message.reply_text("نقاطك لا تكفي")
    if points[u2]<40 and not is_high_rank(u2): return await upd.message.reply_text("خصمك لا يملك نقاط كافية")
    if random.random()<0.5:
        if not is_high_rank(u1): points[u1]+=40
        if not is_high_rank(u2): points[u2]-=40
        await upd.message.reply_text(f"⚔️ {upd.effective_user.first_name} فاز وربح 40 نقطة!")
    else:
        if not is_high_rank(u1): points[u1]-=40
        if not is_high_rank(u2): points[u2]+=40
        await upd.message.reply_text(f"⚔️ {upd.message.reply_to_message.from_user.first_name} فاز وربح 40 نقطة!")
    save()
async def intel(upd,ctx):
    uid=upd.effective_user.id
    if random.random()<0.6:
        if not is_high_rank(uid): points[uid]+=20
        await upd.message.reply_text(f"🃏 +20. رصيدك {points[uid]}")
    else: await upd.message.reply_text("🃏 لا شيء!")
    save()

million_questions = [{"q":"ما عاصمة العراق؟", "a":"بغداد", "points":500},{"q":"كم عدد ألوان قوس قزح؟", "a":"7", "points":300},{"q":"من هو النبي الذي ابتلعه الحوت؟", "a":"يونس", "points":700},{"q":"ما هو الكوكب الأحمر؟", "a":"المريخ", "points":400},{"q":"ما هو أكبر محيط في العالم؟", "a":"الهادي", "points":600}]

async def million(upd,ctx):
    chat = upd.effective_chat.id
    if chat in million_games: return await upd.message.reply_text("هناك جولة مليون جارية!")
    q = random.choice(million_questions)
    million_games[chat] = {"answer":q["a"], "points":q["points"], "started":datetime.now()}
    await upd.message.reply_text(f"🎤 **من سيربح المليون؟**\nالسؤال: {q['q']}\nاربح {q['points']} نقطة! أرسل إجابتك.")
    async def close_later():
        await asyncio.sleep(60)
        if chat in million_games: del million_games[chat]; await ctx.bot.send_message(chat, "⏰ انتهى الوقت! لم يجب أحد.")
    asyncio.create_task(close_later())
async def million_answer(upd,ctx):
    chat = upd.effective_chat.id
    if chat not in million_games: return
    answer = upd.message.text.strip(); game = million_games[chat]
    if answer.lower() == game["answer"].lower():
        uid = upd.effective_user.id
        if not is_high_rank(uid): points[uid] += game["points"]
        save(); await upd.message.reply_text(f"✅ إجابة صحيحة! ربحت {game['points']} نقطة!"); del million_games[chat]
    else: await upd.message.reply_text("❌ إجابة خاطئة! حاول مرة أخرى.")

# ========== الألعاب الجماعية ==========
async def survive(upd,ctx):
    chat = upd.effective_chat.id
    if chat in active_games: return await upd.message.reply_text("هناك لعبة جارية!")
    active_games[chat] = {"players":[], "type":"survive", "started":False, "task":None}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛡️ انضم للتحدي", callback_data="join_survive")], [InlineKeyboardButton("بدء (للمشرف)", callback_data="start_survive")]])
    msg = await upd.message.reply_text("🛡️ **تحدي البقاء** - انضم قبل بدء اللعبة!", reply_markup=kb)
    active_games[chat]["msg"] = msg
async def join_survive(upd,ctx):
    q = upd.callback_query; await q.answer(); uid = q.from_user.id; chat = q.message.chat_id
    if chat not in active_games or active_games[chat]["started"]: return
    if uid not in active_games[chat]["players"]:
        active_games[chat]["players"].append(uid)
        await q.edit_message_text(f"🛡️ **تحدي البقاء** - اللاعبون: {len(active_games[chat]['players'])}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛡️ انضم", callback_data="join_survive")], [InlineKeyboardButton("بدء (للمشرف)", callback_data="start_survive")]]))
async def start_survive(upd,ctx):
    q = upd.callback_query; await q.answer(); uid = q.from_user.id; chat = q.message.chat_id
    if chat not in active_games: return
    member = await ctx.bot.get_chat_member(chat, uid)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]: return
    game = active_games[chat]
    if len(game["players"]) < 2: await q.edit_message_text("تحتاج لاعبين اثنين على الأقل!"); return
    game["started"] = True
    await q.edit_message_text("🛡️ بدأ التحدي! سيتم استبعاد لاعب كل 30 ثانية...")
    async def eliminate():
        players = game["players"][:]
        while len(players) > 1:
            await asyncio.sleep(30)
            eliminated = random.choice(players); players.remove(eliminated)
            await ctx.bot.send_message(chat, f"💀 تم استبعاد {eliminated}! المتبقون: {len(players)}")
        winner = players[0]; points[winner] += 100; save()
        await ctx.bot.send_message(chat, f"🏆 {winner} فاز بتحدي البقاء وربح 100 نقطة!"); del active_games[chat]
    game["task"] = asyncio.create_task(eliminate())

async def grouproulette(upd,ctx):
    chat = upd.effective_chat.id
    if chat in active_games: return await upd.message.reply_text("هناك لعبة جارية!")
    active_games[chat] = {"players":[], "type":"grouproulette", "started":False}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🎰 انضم", callback_data="join_gr")], [InlineKeyboardButton("بدء (مشرف)", callback_data="start_gr")]])
    msg = await upd.message.reply_text("🎰 **روليت جماعي** - كل لاعب يضع 20 نقطة، الخاسر يخسر والبقية يستردون!", reply_markup=kb)
    active_games[chat]["msg"] = msg
async def join_gr(upd,ctx):
    q = upd.callback_query; await q.answer(); uid = q.from_user.id; chat = q.message.chat_id
    if chat not in act
