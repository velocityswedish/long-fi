"""
YouTube Long-Form Video Automation - Bilingual English/Finnish Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Finnish translations
CATEGORIES_FINNISH = {
    "Motivation": "Motivaatio",
    "Love": "Rakkaus",
    "Success": "Menestys",
    "Wisdom": "Viisaus",
    "Happiness": "Onnellisuus",
    "Self Improvement": "Itsensä Kehittäminen",
    "Gratitude": "Kiitollisuus",
    "Friendship": "Ystävyys",
    "Hope": "Toivo",
    "Creativity": "Luovuus",
    "Inner Peace": "Sisäinen Rauha",
    "Confidence": "Itseluottamus",
    "Perseverance": "Sinnikkyys",
    "Inspiration": "Inspiraatio",
    "Positive Life": "Positiivinen Elämä",
    "Courage": "Rohkeus",
    "Kindness": "Ystävällisyys",
    "Patience": "Kärsivällisyys",
    "Forgiveness": "Anteeksianto",
    "Strength": "Voima",
    "Joy": "Ilo",
    "Balance": "Tasapaino",
    "Growth": "Kasvu",
    "Purpose": "Tarkoitus",
    "Mindfulness": "Tietoinen Läsnäolo",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-AndrewNeural"
LANG_VOICE = "fi-FI-NooraNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "finnish": phrase["finnish"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def repair_and_parse_json(content: str):
    """Robustly parse JSON from LLM output with truncation repair and regex recovery."""
    import re
    cleaned = content.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end+1])
        except Exception:
            pass

    if start != -1:
        sub = cleaned[start:]
        last_brace = sub.rfind("}")
        if last_brace != -1:
            try:
                return json.loads(sub[:last_brace+1] + "]")
            except Exception:
                pass

    matches = re.findall(r'\{[^{}]*\"english\"[^{}]*\}', cleaned)
    results = []
    for m in matches:
        try:
            obj = json.loads(m)
            if isinstance(obj, dict) and "english" in obj:
                results.append(obj)
        except Exception:
            continue
    if results:
        return results

    raise ValueError("Could not parse or repair JSON from content")


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_finnish = CATEGORIES_FINNISH[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Finnish.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - ABSOLUTELY ZERO Finnish IN ENGLISH FIELD:
The "english" field must contain ONLY English words. NO Finnish words at all.
The "finnish" field contains the Finnish translation.
The "pronunciation" field is phonetic English spelling approximating Finnish sounds.

These are INSPIRATIONAL PHRASES about the topic, NOT language-learning tips.

WRONG (teaching tip with Finnish words): {{"english": "Don't say 'kiitos,' it's not just 'please.'", ...}}
WRONG (Finnish word in english): {{"english": "Use 'hei' for hello", ...}}
WRONG (lesson tip): {{"english": "Say 'ole hyv\u00e4' for you're welcome", ...}}
CORRECT (pure english phrase): {{"english": "Knowledge is the key to wisdom.", "finnish": "Tieto on avain viisauteen", "pronunciation": "tie-to on a-vain vii-sau-teen"}}
CORRECT: {{"english": "A wise person listens more than they speak.", "finnish": "Viisas ihminen kuuntelee enemm\u00e4n kuin puhuu", "pronunciation": "vii-sas ih-mi-nen kuun-te-lee e-nem-m\u00e4n kuin pu-huu"}}

The english field MUST be 100% English words only. Absolutely NO Finnish words in the english field.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Finnish words) with commas for natural pauses
2. Finnish translation
3. Pronunciation guide (phonetic English spelling)
CRITICAL: Every translation MUST be in Finnish. NEVER use German, Spanish, or any other language. Only Finnish.

Return as JSON array:
[{{"english": "...", "finnish": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You create INSPIRATIONAL PHRASES for YouTube language learning videos. CRITICAL: The 'english' field must be PURE ENGLISH with ZERO Finnish words - no Finnish words at all. These are universal inspirational phrases, NOT language learning tips. Finnish goes ONLY in the 'finnish' field."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = repair_and_parse_json(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    if not all_phrases:
        print(f"[content] AI generation produced 0 phrases. Loading fresh fallback phrases for '{category_english}'...")
        all_phrases = get_fresh_fallback_phrases(category_english, num_phrases)
    elif len(all_phrases) < num_phrases:
        print(f"[content] Only {len(all_phrases)} phrases generated. Padding with fresh fallback phrases...")
        extras = get_fresh_fallback_phrases(category_english, num_phrases - len(all_phrases))
        for ex in extras:
            if ex not in all_phrases:
                all_phrases.append(ex)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "finnish": "Usko itseesi.", "pronunciation": "us-ko it-see-si"},
            {"english": "You are capable of amazing things.", "finnish": "Pystyt upeisiin asioihin.", "pronunciation": "pys-tyt u-pei-siin a-si-oi-hin"},
            {"english": "Dream big, start small.", "finnish": "Unelmoi isosti, aloita pienesti.", "pronunciation": "un-el-moi i-sos-ti a-loi-ta pie-nes-ti"},
            {"english": "Your future is created by your actions.", "finnish": "Tulevaisuutesi luodaan teoillasi.", "pronunciation": "tu-le-vai-suu-te-si luo-daan te-oil-la-si"},
            {"english": "Never give up on your dreams.", "finnish": "\u00c4l\u00e4 koskaan luovuta unelmistasi.", "pronunciation": "a-la kos-kaan luo-vu-ta un-el-mis-ta-si"},
            {"english": "Small steps lead to big changes.", "finnish": "Pienet askeleet johtavat suuriin muutoksiin.", "pronunciation": "pie-net as-ke-leet joh-ta-vat suu-riin muu-tok-siin"},
            {"english": "You are stronger than you think.", "finnish": "Olet vahvempi kuin luulet.", "pronunciation": "o-let vah-vem-pi kuin luu-let"},
        ],
        "Love": [
            {"english": "Love yourself first.", "finnish": "Rakasta itse\u00e4si ensin.", "pronunciation": "ra-kas-ta it-se-a-si en-sin"},
            {"english": "Love makes everything possible.", "finnish": "Rakkaus tekee kaiken mahdolliseksi.", "pronunciation": "rak-kaus te-ke kai-ken mah-dol-li-sek-si"},
            {"english": "My heart beats for you.", "finnish": "Syd\u00e4meni sykkii sinulle.", "pronunciation": "sy-da-me-ni syk-kii si-nul-le"},
            {"english": "You are my everything.", "finnish": "Olet kaikkeni.", "pronunciation": "o-let kaik-ke-ni"},
            {"english": "Together forever, hand in hand.", "finnish": "Yhdess\u00e4 ikuisesti, k\u00e4si k\u00e4dess\u00e4.", "pronunciation": "yh-des-sa i-kui-ses-ti, ka-si ka-des-sa"},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "finnish": "Menestys tulee kovasta ty\u00f6st\u00e4.", "pronunciation": "me-nes-tys tu-lee ko-vas-ta ty-os-ta"},
            {"english": "Keep going, you're getting there.", "finnish": "Jatka vain, olet l\u00e4hell\u00e4.", "pronunciation": "jat-ka vain, o-let la-hel-la"},
            {"english": "Winners never quit.", "finnish": "Voittajat eiv\u00e4t koskaan luovuta.", "pronunciation": "voit-ta-jat ei-vat kos-kaan luo-vu-ta"},
            {"english": "Your effort will pay off.", "finnish": "Vaivann\u00e4k\u00f6si kannattaa.", "pronunciation": "vai-van-na-kos-si kan-nat-taa"},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "finnish": "Tieto on valtaa.", "pronunciation": "tie-to on val-taa"},
            {"english": "Learn from yesterday, live for today.", "finnish": "Opi eilisest\u00e4, el\u00e4 t\u00e4n\u00e4\u00e4n.", "pronunciation": "o-pi ei-li-ses-ta, e-la ta-naan"},
            {"english": "Think before you act.", "finnish": "Ajattele ennen kuin toimit.", "pronunciation": "a-jat-te-le en-nen kuin toi-mit"},
            {"english": "Experience is the best teacher.", "finnish": "Kokemus on paras opettaja.", "pronunciation": "ko-ke-mus on pa-ras o-pet-ta-ja"},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "finnish": "Onnellisuus on valinta.", "pronunciation": "on-ne-li-suus on va-lin-ta"},
            {"english": "Find joy in the little things.", "finnish": "L\u00f6yd\u00e4 ilo pienist\u00e4 asioista.", "pronunciation": "loy-da i-lo pie-nis-ta a-siois-ta"},
            {"english": "Smile, it makes others happy.", "finnish": "Hymyile, se tekee muut onnellisiksi.", "pronunciation": "hy-my-i-le, se te-kee muut on-ne-li-sik-si"},
            {"english": "Today is a gift.", "finnish": "T\u00e4n\u00e4\u00e4n on lahja.", "pronunciation": "ta-naan on lah-ja"},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "finnish": "Ole parempi kuin eilen.", "pronunciation": "o-le pa-rem-pi kuin ei-len"},
            {"english": "Grow through what you go through.", "finnish": "Kasva l\u00e4pik\u00e4ymiesi kokemusten kautta.", "pronunciation": "kas-va la-pi-kay-mi-e-si ko-ke-mus-ten kaut-ta"},
            {"english": "Invest in yourself daily.", "finnish": "Sijoita itseesi p\u00e4ivitt\u00e4in.", "pronunciation": "si-joi-ta it-see-si pai-vit-tain"},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "finnish": "Kiitos kaikesta.", "pronunciation": "kii-tos kai-kes-ta"},
            {"english": "I appreciate your help.", "finnish": "Arvostan apuasi.", "pronunciation": "ar-vos-tan a-pu-a-si"},
            {"english": "Grateful for this moment.", "finnish": "Kiitollinen t\u00e4st\u00e4 hetkest\u00e4.", "pronunciation": "kii-tol-li-nen tas-ta het-kes-ta"},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "finnish": "Yst\u00e4vi\u00e4 ikuisesti, mit\u00e4 tahansa.", "pronunciation": "ys-ta-vi-a i-ku-i-ses-ti mi-ta ta-han-sa"},
            {"english": "You are my best friend.", "finnish": "Olet paras yst\u00e4v\u00e4ni.", "pronunciation": "o-let pa-ras ys-ta-va-ni"},
            {"english": "True friends stick together.", "finnish": "Todelliset yst\u00e4v\u00e4t pit\u00e4v\u00e4t yhteen.", "pronunciation": "to-del-li-set ys-ta-vat pi-ta-vat yh-teen"},
        ],
        "Hope": [
            {"english": "There is always hope.", "finnish": "Toivoa on aina.", "pronunciation": "toi-voa on ai-na"},
            {"english": "Better days are coming.", "finnish": "Parempia p\u00e4ivi\u00e4 on tulossa.", "pronunciation": "pa-rem-pi-a pa-i-vi-a on tu-los-sa"},
            {"english": "Keep faith, keep going.", "finnish": "Pid\u00e4 usko, jatka matkaa.", "pronunciation": "pi-da us-ko, jat-ka mat-kaa"},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "finnish": "Luo jotain kaunista t\u00e4n\u00e4\u00e4n.", "pronunciation": "luo jo-tain kau-nis-ta ta-naan"},
            {"english": "Your imagination is unlimited.", "finnish": "Mielikuvituksesi on rajaton.", "pronunciation": "mie-li-ku-vi-tuk-se-si on ra-ja-ton"},
            {"english": "Art comes from the heart.", "finnish": "Taide tulee syd\u00e4mest\u00e4.", "pronunciation": "tai-de tu-lee sy-da-mes-ta"},
            {"english": "Express yourself freely.", "finnish": "Ilmaise itse\u00e4si vapaasti.", "pronunciation": "il-mai-se it-se-a-si va-paas-ti"},
            {"english": "Innovation starts with curiosity.", "finnish": "Innovaatio alkaa uteliaisuudesta.", "pronunciation": "in-no-vaa-ti-o al-kaa u-te-li-ai-suu-des-ta"},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "finnish": "L\u00f6yd\u00e4 rauha itsest\u00e4si.", "pronunciation": "loy-da rau-ha it-ses-ta-si"},
            {"english": "Breathe, relax, let go.", "finnish": "Hengit\u00e4, rentoudu, p\u00e4\u00e4st\u00e4 irti.", "pronunciation": "hen-gi-ta, ren-tou-du, paas-ta ir-ti"},
            {"english": "Calm mind, happy heart.", "finnish": "Rauhallinen mieli, iloinen syd\u00e4n.", "pronunciation": "rau-hal-li-nen mie-li, i-loi-nen sy-dan"},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "finnish": "Olet tarpeeksi, juuri sellaisena kuin olet.", "pronunciation": "o-let tar-pe-ek-si, juu-ri sel-lai-se-na kuin o-let"},
            {"english": "Stand tall, speak up.", "finnish": "Seiso suorana, puhu rohkeasti.", "pronunciation": "sei-so suo-ra-na, pu-hu roh-ke-as-ti"},
            {"english": "Believe in your abilities.", "finnish": "Usko kykyihisi.", "pronunciation": "us-ko ky-kyi-hi-si"},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "finnish": "\u00c4l\u00e4 koskaan luovuta, jatka ponnistelua.", "pronunciation": "a-la kos-kaan luo-vu-ta, jat-ka pon-nis-te-lu-a"},
            {"english": "Storms make trees take deeper roots.", "finnish": "Myrskyt saavat puut juurtumaan syvemm\u00e4lle.", "pronunciation": "myrs-kyt saa-vat puut juur-tu-maan sy-vem-mal-le"},
            {"english": "Patience and persistence win.", "finnish": "K\u00e4rsiv\u00e4llisyys ja sinnikkyys voittavat.", "pronunciation": "kar-si-val-li-syys ja sin-nik-kyys voit-ta-vat"},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "finnish": "Anna valosi loistaa kirkkaasti.", "pronunciation": "an-na va-lo-si lois-taa kirk-kaas-ti"},
            {"english": "Inspire others by your actions.", "finnish": "Inspiroi muita teoillasi.", "pronunciation": "in-spi-roi mui-ta te-oil-la-si"},
            {"english": "Be the change you want to see.", "finnish": "Ole se muutos, jonka haluat n\u00e4hd\u00e4.", "pronunciation": "o-le se muu-tos, jon-ka ha-lu-at nah-da"},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "finnish": "Valitse positiivisuus joka p\u00e4iv\u00e4.", "pronunciation": "va-lit-se po-si-tii-vi-suus jo-ka pai-va"},
            {"english": "Good vibes only.", "finnish": "Vain hyvi\u00e4 viboja.", "pronunciation": "vain hy-vi-a vi-bo-ja"},
            {"english": "Life is what you make it.", "finnish": "El\u00e4m\u00e4 on sit\u00e4 mit\u00e4 teet siit\u00e4.", "pronunciation": "e-la-ma on si-ta mi-ta teet sii-ta"},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "finnish": "Ole rohkea, ota ensimm\u00e4inen askel.", "pronunciation": "o-le roh-ke-a, o-ta en-sim-mai-nen as-kel"},
            {"english": "Courage is not the absence of fear.", "finnish": "Rohkeus ei ole pelon puuttumista.", "pronunciation": "roh-ke-us ei o-le pe-lon puut-tu-mis-ta"},
            {"english": "Face your fears head on.", "finnish": "Kohtaa pelkosi suoraan.", "pronunciation": "koh-taa pel-ko-si suo-raan"},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "finnish": "Ole yst\u00e4v\u00e4llinen kaikille kohtaamillesi.", "pronunciation": "o-le ys-ta-val-li-nen kai-kil-le koh-taa-mil-le-si"},
            {"english": "Kindness costs nothing, means everything.", "finnish": "Yst\u00e4v\u00e4llisyys ei maksa mit\u00e4\u00e4n, merkitsee kaikkea.", "pronunciation": "ys-ta-val-li-syys ei mak-sa mi-taan, mer-kit-see kaik-ke-a"},
            {"english": "Spread kindness wherever you go.", "finnish": "Levit\u00e4 yst\u00e4v\u00e4llisyytt\u00e4 minne ikin\u00e4 menet.", "pronunciation": "le-vi-ta ys-ta-val-li-syy-ta min-ne i-ki-na me-net"},
        ],
        "Patience": [
            {"english": "Good things take time.", "finnish": "Hyv\u00e4t asiat viev\u00e4t aikaa.", "pronunciation": "hy-vat a-si-at vie-vat ai-kaa"},
            {"english": "Wait patiently, trust the process.", "finnish": "Odota k\u00e4rsiv\u00e4llisesti, luota prosessiin.", "pronunciation": "o-do-ta kar-si-val-li-ses-ti, luo-ta pro-ses-siin"},
            {"english": "Rome wasn't built in a day.", "finnish": "Roomaa ei rakennettu p\u00e4iv\u00e4ss\u00e4.", "pronunciation": "roo-maa ei ra-ken-net-tu pai-vas-sa"},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "finnish": "Anna anteeksi ja vapauta itsesi.", "pronunciation": "an-na an-teek-si ja va-pau-ta it-se-si"},
            {"english": "Let go of grudges, find peace.", "finnish": "P\u00e4\u00e4st\u00e4 irti kaunasta, l\u00f6yd\u00e4 rauha.", "pronunciation": "paas-ta ir-ti kau-nas-ta, loy-da rau-ha"},
            {"english": "Forgiveness is a gift to yourself.", "finnish": "Anteeksianto on lahja itsellesi.", "pronunciation": "an-teek-si-an-to on lah-ja it-sel-le-si"},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "finnish": "Olet vahvempi kuin uskotkaan.", "pronunciation": "o-let vah-vem-pi kuin us-kot-kaan"},
            {"english": "Inner strength comes from within.", "finnish": "Sis\u00e4inen voima tulee sis\u00e4lt\u00e4.", "pronunciation": "si-sai-nen voi-ma tu-lee si-sal-ta"},
            {"english": "Challenges make you stronger.", "finnish": "Haasteet tekev\u00e4t sinusta vahvemman.", "pronunciation": "haas-teet te-ke-vat si-nus-ta vah-vem-man"},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "finnish": "L\u00f6yd\u00e4 ilo joka hetkest\u00e4.", "pronunciation": "loy-da i-lo jo-ka het-kes-ta"},
            {"english": "Joy is contagious, spread it.", "finnish": "Ilo on tarttuvaa, levit\u00e4 sit\u00e4.", "pronunciation": "i-lo on tart-tu-vaa, le-vi-ta si-ta"},
            {"english": "Dance like nobody's watching.", "finnish": "Tanssi kuin kukaan ei katsoisi.", "pronunciation": "tans-si kuin ku-kaan ei kat-soi-si"},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "finnish": "L\u00f6yd\u00e4 tasapaino el\u00e4m\u00e4ss\u00e4si.", "pronunciation": "loy-da ta-sa-pai-no e-la-mas-sa-si"},
            {"english": "Work hard, rest well.", "finnish": "Ty\u00f6skentele kovasti, lep\u00e4\u00e4 hyvin.", "pronunciation": "tyos-ken-te-le ko-vas-ti, le-paa hy-vin"},
            {"english": "Too much of anything is not good.", "finnish": "Liikaa mit\u00e4 tahansa ei ole hyv\u00e4ksi.", "pronunciation": "lii-kaa mi-ta ta-han-sa ei o-le hy-vak-si"},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "finnish": "Kasvu tapahtuu mukavuusalueen ulkopuolella.", "pronunciation": "kas-va ta-pah-tuu mu-ka-vuus-a-lu-een ul-ko-puo-lel-la"},
            {"english": "Embrace change, grow stronger.", "finnish": "Hyv\u00e4ksy muutos, vahvistu.", "pronunciation": "hy-vak-sy muu-tos, vah-vis-tu"},
            {"english": "Every challenge is a chance to grow.", "finnish": "Jokainen haaste on mahdollisuus kasvaa.", "pronunciation": "jo-kai-nen haas-te on mah-dol-li-suus kas-vaa"},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "finnish": "L\u00f6yd\u00e4 tarkoituksesi, seuraa sit\u00e4.", "pronunciation": "loy-da tar-koi-tuk-se-si, seu-raa si-ta"},
            {"english": "Your life has meaning.", "finnish": "El\u00e4m\u00e4ll\u00e4si on tarkoitus.", "pronunciation": "e-la-mal-la-si on tar-koi-tus"},
            {"english": "Live with intention, not accident.", "finnish": "El\u00e4 tarkoituksella, ei sattumalta.", "pronunciation": "e-la tar-koi-tuk-sel-la, ei sat-tu-mal-ta"},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "finnish": "Ole l\u00e4sn\u00e4 t\u00e4ss\u00e4 hetkess\u00e4.", "pronunciation": "o-le las-na tas-sa het-kes-sa"},
            {"english": "Breathe deeply, stay grounded.", "finnish": "Hengit\u00e4 syv\u00e4\u00e4n, pysy maadoitettuna.", "pronunciation": "hen-gi-ta sy-vaan, py-sy maa-doi-tet-tu-na"},
            {"english": "Notice the little things around you.", "finnish": "Huomaa pienet asiat ymp\u00e4rill\u00e4si.", "pronunciation": "huo-maa pie-net a-si-at ym-pa-ril-la-si"},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str, retries: int = 3):
    import edge_tts
    for attempt in range(retries):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            if Path(output_path).exists() and Path(output_path).stat().st_size > 300:
                return True
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(0.8 * (attempt + 1))
            else:
                print(f"  TTS error after {retries} attempts: {e}")
    return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["finnish"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a]apad=pad_dur=0.5[a0];[a0][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    finnish = phrase_data.get("finnish", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(finnish, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Finnish Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY FINNISH"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_finnish: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER FINNISH", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_finnish, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 TÄRKEÄÄ LAUSETTA"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY FINNISH", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_finnish: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Finnish in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_finnish})",
        f"60 Finnish Phrases for {category_english} | Speak Finnish Like a Native! ({category_finnish})",
        f"Master Finnish {category_english} | 60 Essential Finnish Phrases with Pronunciation | Velocity Finnish",
        f"Finnish Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Finnish Fluently | {category_english} Phrases | English + Finnish + Pronunciation",
    ]

    description = f"""\U0001F1EB\U0001F1EE Learn Finnish with Velocity Finnish! \U0001F1EB\U0001F1EE

In this video, you'll learn 60 essential Finnish phrases about {category_english} ({category_finnish}).
Perfect for beginners and intermediate learners!

\U0001F4DA WHAT YOU'LL LEARN:
\u2022 60 practical {category_english} phrases in Finnish
\u2022 Correct pronunciation guide
\u2022 Natural pauses for speaking practice
\u2022 Common expressions used by native speakers

\U0001F551 VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
\U0001F4DD ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Finnish: {phrase['finnish']}
    Pronunciation: {phrase['pronunciation']}
"""

    description += """
\U0001F3AF PERFECT FOR:
\u2022 Finnish beginners wanting to expand vocabulary
\u2022 Intermediate learners practicing pronunciation
\u2022 Anyone interested in Finnish language and culture
\u2022 Language enthusiasts and polyglots
\u2022 Students preparing for exams

\U0001F4A1 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

\U0001F514 SUBSCRIBE for more Finnish learning content!
\U0001F44D LIKE this video if you found it helpful!
\U0001F4AC COMMENT which phrases you want to learn next!

\U0001F4F1 FOLLOW VELOCITY FINNISH:
[Add your social media links here]

\U0001F3B5 MUSIC:
[Add music credits if applicable]

\U0001F4D6 RELATED VIDEOS:
\u2022 Finnish Motivation Phrases
\u2022 Finnish Love Expressions
\u2022 Basic Finnish Greetings

#LearnFinnish #FinnishPhrases #FinnishLanguage #{category_english.replace(' ', '')} #VelocityFinnish #FinnishForBeginners #SpeakFinnish #FinnishVocabulary #Pronunciation #LanguageLearning #Finnish101 #FinnishLesson

---
\u00A9 Velocity Finnish - Making Finnish learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Finnish",
            "Finnish Phrases",
            "Finnish Language",
            category_english,
            "Velocity Finnish",
            "Finnish for Beginners",
            "Speak Finnish",
            "Finnish Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Finnish 101",
            "Finnish Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_finnish": category_finnish,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_FINNISH[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['finnish']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_FINNISH[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_FINNISH[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"
    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_FINNISH[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Finnish: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Finnish", "Finnish Phrases", "Finnish", category_english, "Velocity Finnish"],
        "category_english": category_english,
        "category_finnish": CATEGORIES_FINNISH[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Finnish")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Finnish YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY FINNISH - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_FINNISH[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)