import streamlit as st
from PIL import Image
import pytesseract
import re
import cv2
import numpy as np
from rapidfuzz import fuzz

# --- CONFIG ---
st.set_page_config(page_title="Food Scanner", page_icon="🔍")

# --- E NUMBERS DATABASE ---
E_NUMBERS = {
    "E102": ("Тартразин", "⚠️ може да предизвика алергии", 2),
    "E110": ("Жълто оцветител", "⚠️ потенциално вреден", 2),
    "E124": ("Понсо 4R", "⚠️ свързва се с хиперактивност", 3),
    "E129": ("Оцветител", "⚠️ алергичен риск", 2),
    "E621": ("MSG", "⚠️ може да причини главоболие", 2),
    "E951": ("Аспартам", "⚠️ спорен подсладител", 3),
    "E952": ("Цикламат", "⛔ забранен в някои държави", 3),
    "E954": ("Сахарин", "⚠️ потенциален риск", 2),
}

# --- INGREDIENT DATABASE ---
HARMFUL_INGREDIENTS = {
    "palm oil": ("Палмово масло", "⚠️ свързва се със сърдечни проблеми", 2),
    "палмово масло": ("Палмово масло", "⚠️ потенциален риск", 2),
    "hydrogenated": ("Хидрогенирани мазнини", "⛔ транс мазнини", 3),
    "aspartame": ("Аспартам", "⚠️ спорен подсладител", 3),
    "high fructose corn syrup": ("HFCS", "⚠️ риск от затлъстяване", 3),
    "monosodium glutamate": ("MSG", "⚠️ подобрител на вкуса", 2),
    "глутамат": ("MSG", "⚠️ подобрител на вкуса", 2),
    "sodium nitrite": ("Нитрит", "⛔ свързва се с рак", 3),
    "нитрит": ("Нитрит", "⛔ потенциален канцероген", 3),
    "sodium nitrate": ("Нитрат", "⚠️ потенциален риск", 2),
    "artificial flavor": ("Изкуствени аромати", "⚠️ неясен състав", 2),
    "artificial color": ("Оцветители", "⚠️ потенциално вредни", 2),
    "консерванти"
}

# --- IMAGE PREPROCESS ---
def preprocess_image(image):
    img = np.array(image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

# --- OCR ---
def extract_text(image):
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(processed, lang='eng')
    return text

# --- FIND E NUMBERS ---
def find_e_numbers(text):
    pattern = r"E[\s\-]?\d{3}"
    matches = re.findall(pattern, text.upper())
    
    cleaned = []
    for m in matches:
        m = m.replace(" ", "").replace("-", "")
        cleaned.append(m)
        
    return list(set(cleaned))

# --- FIND INGREDIENTS ---
def find_ingredients(text):
    found = []
    text_lower = text.lower()

    for key, value in HARMFUL_INGREDIENTS.items():
        score = fuzz.partial_ratio(key, text_lower)
        if score > 85:
            found.append(value)

    return list(set(found))

# --- RISK SCORE ---
def calculate_risk(e_list, ing_list):
    score = 0
    
    for e in e_list:
        if e in E_NUMBERS:
            score += E_NUMBERS[e][2]
    
    for ing in ing_list:
        score += ing[2]
    
    return score

# --- UI ---
st.title("🔍 Food Label Scanner")
st.write("Качи снимка на етикет и открий вредни съставки")

uploaded_file = st.file_uploader("📸 Качи изображение", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Качено изображение", use_column_width=True)

    with st.spinner("🔍 Анализ..."):
        text = extract_text(image)

    st.subheader("📄 Разпознат текст")
    st.text(text)

    # --- E NUMBERS ---
    st.subheader("🧪 Е-та")
    e_numbers = find_e_numbers(text)

    if e_numbers:
        for e in e_numbers:
            if e in E_NUMBERS:
                name, desc, risk = E_NUMBERS[e]
                st.error(f"{e} ({name}) → {desc}")
            else:
                st.warning(f"{e} → няма данни")
    else:
        st.success("Няма открити Е-та")

    # --- INGREDIENTS ---
    st.subheader("⚠️ Други съставки")
    ingredients = find_ingredients(text)

    if ingredients:
        for name, desc, risk in ingredients:
            st.error(f"{name} → {desc}")
    else:
        st.success("Няма открити рискови съставки")

    # --- RISK ---
    risk_score = calculate_risk(e_numbers, ingredients)

    st.subheader("📊 Оценка на риска")

    if risk_score == 0:
        st.success("🟢 Нисък риск")
    elif risk_score < 5:
        st.warning("🟡 Среден риск")
    else:
        st.error("🔴 Висок риск")
