# 🔁 Your existing imports remain unchanged
import os
import io
import random
import pdfplumber
import docx
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from gtts import gTTS
from TTS.api import TTS
from transformers import pipeline

st.set_page_config(page_title="Document Analyzer", layout="centered")

load_dotenv()

summarizer = pipeline("summarization", model="csebuetnlp/mT5_multilingual_XLSum")

# Initialize session state
if 'summary' not in st.session_state:
    st.session_state.summary = ''
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None
if 'editable_summary' not in st.session_state:
    st.session_state.editable_summary = ''

LABELS = {
    "en": {
        "title": "📄 Document Analyzer",
        "subheading": "Summarize your documents and listen to them in voice",
        "upload": "Upload a document (PDF or DOCX)",
        "generate": "⚙️ Generate Summary",
        "read": "🔊 Read Summary",
        "switch_lang": "🔁 Switch Language (English/Marathi)",
        "summary_header": "📝 Summary"
    },
    "mr": {
        "title": "📄 दस्तऐवज विश्लेषक",
        "subheading": "आपले दस्तऐवज संक्षेप करा आणि त्यांना आवाजात ऐका",
        "upload": "दस्तऐवज अपलोड करा (PDF किंवा DOCX)",
        "generate": "⚙️ सारांश तयार करा",
        "read": "🔊 सारांश वाचा",
        "switch_lang": "🔁 भाषा बदला (मराठी/English)",
        "summary_header": "📝 सारांश"
    }
}

FRIENDLY_MESSAGES = [
    "Take a deep breath 🌬️",
    "I Think you should drink some water 💧",
    "Umm...Give your eyes a blink 👁️",
    "We’re working on your file ⏳",
    "Summarizing your document 📄",
    "Organizing important points 🧠"
]

spinner_placeholder = st.empty()

def show_friendly_spinner(msg):
    spinner_placeholder.markdown(f"""
        <div class="custom-spinner">
            <div class="spinner-box">{msg}</div>
        </div>
        <style>
        .custom-spinner {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0, 0, 0, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }}
        .spinner-box {{
            background-color: #222;
            color: white;
            border-radius: 12px;
            padding: 30px 50px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            font-size: 22px;
            font-weight: 600;
            font-family: 'Segoe UI Emoji', sans-serif;
        }}
        </style>
    """, unsafe_allow_html=True)

def remove_spinner():
    spinner_placeholder.empty()

def extract_text(uploaded_file):
    text = ""
    if uploaded_file.name.endswith(".pdf"):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()

def summarize_text(text):
    try:
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        summary = ""
        spinner_msg = random.choice(FRIENDLY_MESSAGES)
        show_friendly_spinner(spinner_msg)
        for chunk in chunks:
            result = summarizer(chunk, max_length=120, min_length=50, do_sample=False)
            summary += result[0]['summary_text'] + " "
        remove_spinner()
        return summary.strip()
    except Exception as e:
        remove_spinner()
        return f"⚠️ Summarization error: {e}"

def translate_text(text, target_lang):
    try:
        return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception as e:
        return f"⚠️ Translation error: {e}"

def speak_text(text, lang='en'):
    try:
        if lang == 'en':
            tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            tts.tts_to_file(text=text, file_path="output.wav")
            with open("output.wav", "rb") as f:
                st.audio(f.read(), format='audio/wav')
        else:
            raise ValueError("Offline voice cloning only supports English")
    except Exception as e:
        st.warning(f"⚠️ Using Google TTS instead. Reason: {e}")
        speak_text_google(text, lang)

def speak_text_google(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        st.audio(audio_fp, format='audio/mp3')
    except Exception as e:
        st.error(f"Audio failed: {e}")

# === UI ===
lang = st.session_state.language
labels = LABELS[lang]

st.title(labels["title"])
st.caption(labels["subheading"])

uploaded_file = st.file_uploader(labels["upload"], type=["pdf", "docx"])

# Reset state if a new file is uploaded
if uploaded_file != st.session_state.last_uploaded_file:
    st.session_state.summary = ''
    st.session_state.editable_summary = ''
    st.session_state.last_uploaded_file = uploaded_file

if st.checkbox(labels["switch_lang"]):
    st.session_state.language = 'mr' if lang == 'en' else 'en'
    st.rerun()

if uploaded_file and st.button(labels["generate"]):
    raw_text = extract_text(uploaded_file)
    if not raw_text.strip():
        st.error("⚠️ No text found in document.")
    else:
        summary = summarize_text(raw_text)
        if st.session_state.language == 'mr':
            summary = translate_text(summary, 'mr')
        st.session_state.summary = summary
        st.session_state.editable_summary = summary  # ✅ Initialize before text_area

# ✅ Show editable summary safely
if st.session_state.summary:
    st.subheader(labels["summary_header"])
    editable_text = st.text_area("Edit your summary below if needed:", 
                                 value=st.session_state.editable_summary, 
                                 height=250)
    if editable_text != st.session_state.editable_summary:
        st.session_state.editable_summary = editable_text

    target_lang = 'mr' if st.session_state.language == 'en' else 'en'
    button_label = f"🌐 Translate Summary to {'Marathi' if target_lang == 'mr' else 'English'}"

    if st.button(button_label):
        try:
            translated = translate_text(st.session_state.editable_summary, target_lang)
            st.session_state.summary = translated
            st.session_state.editable_summary = translated
            st.success("✅ Summary translated successfully.")
        except Exception as e:
            st.error(f"⚠️ Could not translate: {e}")

if st.button(labels["read"]):
    show_friendly_spinner("🎧 Generating your voice... Please relax!")
    speak_text(st.session_state.editable_summary, lang='mr' if st.session_state.language == 'mr' else 'en')
    remove_spinner()

st.markdown("---")
st.markdown("<p style='text-align:center;'>© 2025 Designed and developed by Soha Mujawar</p>", unsafe_allow_html=True)
