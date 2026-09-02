import streamlit as st
import pandas as pd
import os
import zipfile
import io
import re
from PIL import Image
import google.generativeai as genai

# Must be the first Streamlit command
st.set_page_config(page_title="UCL Image Auto-Renamer", layout="wide", page_icon="⚽")

# --- PREMIUM UI & VIDEO BACKGROUND INJECTION ---
st.markdown("""
<style>
/* Import UEFA-style fonts */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800;900&display=swap');

/* Hide default Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {background-color: transparent !important;}

/* Glassmorphism for main container */
.block-container {
    background: rgba(4, 15, 45, 0.7) !important;
    backdrop-filter: blur(15px) !important;
    -webkit-backdrop-filter: blur(15px) !important;
    border: 1px solid rgba(0, 229, 255, 0.15);
    border-radius: 20px;
    box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.6);
    padding: 3rem !important;
    margin-top: 3rem !important;
    margin-bottom: 3rem !important;
    max-width: 900px !important;
}

/* Typography matching UCL brand */
h1, h2, h3, p, label, .stRadio > div, .stMarkdown, .stText {
    font-family: 'Montserrat', sans-serif !important;
    color: #ffffff !important;
}

/* Glowing Title */
h1 {
    text-align: center;
    text-transform: uppercase;
    font-weight: 900 !important;
    background: linear-gradient(to right, #ffffff, #00e5ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0px 4px 30px rgba(0, 229, 255, 0.5);
    margin-bottom: 2rem !important;
    letter-spacing: 2px;
}

/* Custom Buttons (The UCL Flow) */
.stButton > button {
    background: linear-gradient(90deg, #001489 0%, #00e5ff 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 30px !important;
    padding: 0.75rem 2.5rem !important;
    font-weight: 800 !important;
    text-transform: uppercase;
    box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 8px 30px rgba(0, 229, 255, 0.6) !important;
}

/* Premium File Uploader */
[data-testid="stFileUploadDropzone"] {
    background-color: rgba(255, 255, 255, 0.03) !important;
    border: 2px dashed rgba(0, 229, 255, 0.3) !important;
    border-radius: 15px !important;
    transition: all 0.3s ease !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    background-color: rgba(0, 229, 255, 0.1) !important;
    border-color: #00e5ff !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: rgba(0, 10, 30, 0.85) !important;
    backdrop-filter: blur(10px) !important;
    border-right: 1px solid rgba(0, 229, 255, 0.2);
}

/* Inputs and text areas */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background-color: rgba(255,255,255,0.05) !important;
    color: white !important;
    border: 1px solid rgba(0, 229, 255, 0.3) !important;
    border-radius: 10px !important;
}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border: 1px solid #00e5ff !important;
    box-shadow: 0 0 10px rgba(0, 229, 255, 0.3) !important;
}
</style>

<!-- Background Video (Replace src with any raw direct MP4 link of a UCL hype video) -->
<video autoplay loop muted playsinline style="position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%; z-index: -100; object-fit: cover; filter: brightness(0.25) contrast(1.3) sepia(0.3) hue-rotate(180deg);">
  <source src="https://cdn.pixabay.com/video/2024/02/16/108390-679958971_large.mp4" type="video/mp4">
</video>
""", unsafe_allow_html=True)


st.title("⭐ UCL Auto-Renamer")

# --- SIDEBAR: SETTINGS ---
st.sidebar.markdown("### ⚙️ SYSTEM SETTINGS")
mode = st.sidebar.radio("RECOGNITION ENGINE", ["Gemini AI Vision", "Filename Matching"])

api_key = ""
if mode == "Gemini AI Vision":
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.sidebar.success("✅ Secure AI Uplink Active")
    else:
        api_key = st.sidebar.text_input("Gemini API Key", type="password")

# --- HELPER: NORMALIZE COLUMNS ---
def normalize_df(df):
    col_map = {}
    for col in df.columns:
        c_lower = str(col).strip().lower()
        if 'player' in c_lower or 'name' in c_lower: col_map[col] = 'Player'
        elif 'team' in c_lower or 'club' in c_lower: col_map[col] = 'Team'
        elif 'number' in c_lower or 'num' in c_lower or c_lower == '#': col_map[col] = 'Number'
    return df.rename(columns=col_map)

# --- HELPER: PARSE PASTED TEXT ---
def parse_pasted_text(text, default_team="AEK Athens"):
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    if not lines: return None
    rows = []
    
    if any('|' in line for line in lines):
        for l in [x for x in lines if not all(c in '|- :' for c in x)]:
            parts = [p.strip() for p in l.split('|') if p.strip()]
            if len(parts) >= 3: rows.append({'Player': parts[0], 'Team': parts[1], 'Number': parts[2]})
            elif len(parts) == 2: rows.append({'Player': parts[0], 'Team': default_team, 'Number': parts[1]})
    else:
        for line in lines:
            m_start = re.match(r'^(\d+)\s+(.+)$', line)
            if m_start:
                rows.append({'Player': m_start.group(2).strip(), 'Team': default_team, 'Number': m_start.group(1).strip()})
    
    return pd.DataFrame(rows) if rows else None

# --- SQUAD DATABASE ---
st.markdown("### 1. LOAD SQUAD DATA")
db_col1, db_col2 = st.columns(2)
db_input_method = db_col1.radio("Source", ["Upload File", "Paste Roster"], horizontal=True)

df_db = None
if db_input_method == "Upload File":
    db_file = st.file_uploader("Drop Excel (.xlsx) / CSV", type=["xlsx", "csv"])
    if db_file:
        df_raw = pd.read_excel(db_file) if db_file.name.endswith(".xlsx") else pd.read_csv(db_file)
        df_db = normalize_df(df_raw)
else:
    default_team_input = st.text_input("Fallback Team Name", value="Real Madrid")
    pasted_text = st.text_area("Paste Raw Text", height=100)
    if pasted_text: df_db = parse_pasted_text(pasted_text, default_team=default_team_input)

if df_db is not None and not df_db.empty:
    st.success(f"✓ Roster Synced: {len(df_db)} Athletes")

st.markdown("<br>", unsafe_allow_html=True)

# --- IMAGE ASSETS ---
st.markdown("### 2. INJECT ASSETS")
uploaded_files = st.file_uploader("Drop Images or a ZIP Folder", type=["png", "jpg", "jpeg", "webp", "zip"], accept_multiple_files=True)

images_to_process = {}
if uploaded_files:
    for f in uploaded_files:
        if f.name.lower().endswith(".zip"):
            with zipfile.ZipFile(f, 'r') as z:
                for file_info in z.infolist():
                    if not file_info.is_dir() and not file_info.filename.startswith('__MACOSX'):
                        if file_info.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            images_to_process[file_info.filename] = z.read(file_info)
        else:
            images_to_process[f.name] = f.read()

# --- GEMINI VISION ---
def identify_with_gemini(image_bytes, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(io.BytesIO(image_bytes))
    prompt = "Identify the soccer player in this image. Return ONLY their full name and club team in this exact format: Player Name, Team Name."
    response = model.generate_content([prompt, img])
    parts = response.text.strip().split(",")
    return parts[0].strip() if len(parts) > 0 else response.text.strip()

# --- EXECUTION ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("INITIALIZE SEQUENCE"):
    if df_db is None or df_db.empty: st.error("Database missing.")
    elif not images_to_process: st.error("Assets missing.")
    else:
        zip_buffer = io.BytesIO()
        processed = 0
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
            bar = st.progress(0)
            items = list(images_to_process.items())
            
            for idx, (img_path, img_bytes) in enumerate(items):
                filename = os.path.basename(img_path)
                folder_dir = os.path.dirname(img_path)
                ext = os.path.splitext(filename)[1]
                player_matched = None
                
                if mode == "Gemini AI Vision":
                    try:
                        detected_name = identify_with_gemini(img_bytes, api_key)
                        matches = df_db[df_db['Player'].str.contains(detected_name, case=False, na=False)]
                        if not matches.empty: player_matched = matches.iloc[0]
                    except: pass
                else:
                    for _, row in df_db.iterrows():
                        if str(row['Player']).lower() in filename.lower():
                            player_matched = row
                            break

                if player_matched is not None:
                    out_path = os.path.join(folder_dir, f"{player_matched['Number']}{ext}") if folder_dir else f"{player_matched['Number']}{ext}"
                    zip_out.writestr(out_path, img_bytes)
                    processed += 1
                bar.progress((idx + 1) / len(items))

        if processed > 0:
            st.balloons()
            st.download_button("🏆 DOWNLOAD ASSETS (.ZIP)", data=zip_buffer.getvalue(), file_name="UCL_Renamed_Assets.zip", mime="application/zip")
