import streamlit as st
import requests
import os
import random
import google.generativeai as genai
from dotenv import load_dotenv
from gtts import gTTS
import base64

# 1. إعدادات البيئة
load_dotenv()
BASE_URL = os.getenv("NOCODB_BASE_URL")
TOKEN = os.getenv("NOCODB_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# إعداد Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. كود تجميل الواجهة
st.set_page_config(page_title="مغامرة صوفي وريمي", page_icon="✨", layout="centered")

st.markdown("""
    <style>
    .stAlert { border-radius: 15px !important; border: 2px solid #e0e0e0 !important; }
    h1, h2, h3 { color: #2c3e50 !important; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { border-radius: 25px !important; border: 1px solid #4a90e2 !important; transition: 0.3s; }
    .stButton>button:hover { background-color: #4a90e2 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# دالة لتحويل النص إلى صوت وعرضه في Streamlit
import base64

def speak_french(text):
    try:
        tts = gTTS(text=text, lang='fr')
        tts.save("hint.mp3")
        
        with open("hint.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            
        # إضافة واجهة صوتية واضحة جداً مع زر تشغيل يدوي كاحتياط
        audio_tag = f"""
            <div style="background-color: #f0f2f6; border-radius: 10px; padding: 10px; margin-top: 10px;">
                <p style="margin: 0; font-size: 0.8em; color: #666;">🔊 استمع للنصيحة الفرنسية:</p>
                <audio controls autoplay style="width: 100%;">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
            </div>
        """
        st.markdown(audio_tag, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"خطأ في معالجة الصوت: {e}")


# 3. دالة جلب البيانات
def fetch_v3_data(table_id):
    headers = {"xc-token": TOKEN}
    url = f"{BASE_URL}/{table_id}/records"
    try:
        response = requests.get(url, headers=headers)
        return response.json().get('records', [])
    except:
        return []

# 4. واجهة التطبيق
st.title("🧼 مغامرة صوفي وريمي الذكية")
st.write("تعلم اللغة الفرنسية برقي وإبداع ✨")

if st.button("✨ ابدأ تحدياً جديداً"):
    tpl_id = "mn4mjg7rmrvcu17"
    res_id = "ms66xirghynwh9d"
    
    templates = fetch_v3_data(tpl_id)
    resources = fetch_v3_data(res_id)

    if templates and resources:
        tpl_fields = random.choice(templates)['fields']
        res_fields = random.choice(resources)['fields']
        
        st.session_state['verb'] = res_fields.get('Res_Target_Verb', "")
        st.session_state['expected'] = res_fields.get('Res_Expected_Result', "")
        st.session_state['feedback'] = res_fields.get('Res_Persona_Feedback', "")
        st.session_state['teacher'] = tpl_fields.get('Temp_System_Persona_Ref', "Sophie")
        
        prompt_raw = tpl_fields.get('Temp_Structural_Prompt', "")
        sentence = res_fields.get('Res_Context_Sentence', "").replace("{Verb}", f"({st.session_state['verb']})")
        st.session_state['full_q'] = prompt_raw.replace("{Sentence}", sentence).replace("{Verb}", st.session_state['verb'])
        
        if 'current_hint' in st.session_state: del st.session_state['current_hint']
        st.rerun()

# 5. عرض السؤال والتحقق
if 'full_q' in st.session_state:
    st.markdown("---")
    st.info(f"🧑‍🏫 المعلم المساعد: **{st.session_state['teacher']}**")
    
    # تنظيف النص للعرض
    clean_q = st.session_state['full_q'].replace("\\n", "\n").replace("{Input_Field}", "✍️ __________")
    st.markdown(f"### {clean_q}")
    
    # تعريف حقل الإدخال هنا ليكون متاحاً لزر التحقق
    user_input = st.text_input("اكتب إجابتك هنا:", key="ans_input")
    
    if st.button("تحقق ✅"):
        expected = str(st.session_state['expected']).strip().lower()
        actual = user_input.strip().lower()
        
        if actual == expected:
            st.balloons()
            st.success(f"🌟 مذهل! {st.session_state['feedback']}")
            speak_french(st.session_state['feedback'])
        else:
            with st.spinner(f"✨ {st.session_state['teacher']} يراجع إجابتك..."):
                prompt_ai = f"""
                Tu es {st.session_state['teacher']}, un ami français élégant.
                Réponds EXCLUSIVEMENT en FRANÇAIS.
                L'élève a écrit '{actual}' au lieu de '{expected}'.
                Donne un indice court (max 20 mots), encourageant et chic.
                Ne donne jamais la réponse.
                """
                try:
                    response = model.generate_content(prompt_ai)
                    st.session_state['current_hint'] = response.text
                    
                    st.warning("🧐 لمسة سحرية ناقصة...")
                    st.info(f"✨ نصيحة من {st.session_state['teacher']}: \n\n {st.session_state['current_hint']}")
                    speak_french(st.session_state['current_hint'])
                except Exception as e:
                    st.error("أوه! تعذر الاتصال بالذكاء الاصطناعي.")