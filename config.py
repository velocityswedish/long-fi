"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY FINNISH"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "FINNISH"
HANDLE = "@velocityfinnish"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'fi',
 'name': 'Finnish',
 'native_name': 'Suomi',
 'history_key': 'finnish',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'fi-FI-NooraNeural',
 'native_fallback_voice': 'fi-FI-HarriNeural',
 'native_engine': 'edge',
 'native_lang_code': 'fi',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'SUOMI',
 'translit_label': 'SAY IT LIKE',
 'flag': 'fi',
 'greeting': 'Hei!',
 'encouragement': 'Loistavaa!',
 'rtl': False,
 'char_tiles': False,
 'script_font': '',
 'glyphs': 'ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖåäö'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'Motivaatio',
 'Love': 'Rakkaus',
 'Success': 'Menestys',
 'Wisdom': 'Viisaus',
 'Happiness': 'Onnellisuus',
 'Self Improvement': 'Itsensä Kehittäminen',
 'Gratitude': 'Kiitollisuus',
 'Friendship': 'Ystävyys',
 'Hope': 'Toivo',
 'Creativity': 'Luovuus',
 'Inner Peace': 'Sisäinen Rauha',
 'Confidence': 'Itseluottamus',
 'Perseverance': 'Sinnikkyys',
 'Inspiration': 'Inspiraatio',
 'Positive Life': 'Positiivinen Elämä',
 'Courage': 'Rohkeus',
 'Kindness': 'Ystävällisyys',
 'Patience': 'Kärsivällisyys',
 'Forgiveness': 'Anteeksianto',
 'Strength': 'Voima',
 'Joy': 'Ilo',
 'Balance': 'Tasapaino',
 'Growth': 'Kasvu',
 'Purpose': 'Tarkoitus',
 'Mindfulness': 'Tietoinen Läsnäolo',
 'Travel & Airport': 'Matkustus & lentokenttä',
 'Ordering Food & Dining': 'Ruokatilaukset & ruokailu',
 'Shopping & Prices': 'Ostokset & hinnat',
 'Asking for Directions': 'Tien kysyminen',
 'Hotel & Accommodation': 'Hotelli & majoitus',
 'Daily Routine': 'Päivittäiset rutiinit',
 'Meeting People & Greetings': 'Ihmisten tapaaminen & tervehdykset',
 'Emergency & Health': 'Hätätilanteet & terveys',
 'Public Transportation': 'Julkinen liikenne',
 'Work & Office': 'Työ & toimisto',
 'Weather & Small Talk': 'Sää & small talk',
 'Coffee Shop & Bakery': 'Kahvila & leipomo',
 'Family & Home': 'Perhe & koti',
 'Hobbies & Free Time': 'Harrastukset & vapaa-aika',
 'Dating & Romance': 'Treffit & romantiikka',
 'Phone Calls & Messages': 'Puhelut & viestit',
 'Banking & Money': 'Pankkiasiat & raha',
 'Doctor & Pharmacy': 'Lääkäri & apteekki',
 'Sports & Fitness': 'Urheilu & kuntoilu',
 'Celebrations & Parties': 'Juhlat & illanvietot',
 'Feelings & Emotions': 'Tunteet',
 'Agreeing & Disagreeing': 'Samaa & eri mieltä oleminen',
 'Making Plans': 'Suunnitelmien tekeminen',
 'Common Native Slang': 'Yleinen puhekielinen slangisanasto',
 'Cultural Traditions': 'Kulttuurilliset perinteet'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnfinnish',
 '#finnishlessons',
 '#finnishforbeginners',
 '#languagelearning',
 '#finnishvocabulary',
 '#velocityfinnish',
 '#dailyfinnish',
 '#finnish',
 '#learnlanguages',
 '#speakfinnish']
# ==== HASHTAGS END ====
