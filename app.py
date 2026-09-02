import streamlit as st
import pandas as pd
import os
import zipfile
import io
import re
import base64
from PIL import Image
import google.generativeai as genai

# Must be the first Streamlit command
st.set_page_config(page_title="Squad Image Studio", layout="wide", page_icon="⭐")

# --- STYLE ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap');

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {background-color: transparent !important;}

.stApp {
    background: #050914 !important;
}

.block-container {
    background: rgba(9, 15, 34, 0.6) !important;
    border: 1px solid rgba(180, 195, 230, 0.10);
    border-radius: 8px;
    box-shadow: 0 30px 80px rgba(0,0,0,0.55);
    padding: 3rem !important;
    padding-top: 0 !important;
    margin-top: 2.5rem !important;
    margin-bottom: 3rem !important;
    max-width: 920px !important;
    overflow: hidden;
}

h1, h2, h3, p, label, .stRadio > div, .stMarkdown, .stText, span {
    font-family: 'Inter', sans-serif !important;
    color: #dde3f5 !important;
}

/* ---------------- FULL-BLEED CINEMATIC HERO ---------------- */
.hero-bleed {
    position: relative;
    margin: 0 -3rem 2.6rem -3rem;
    padding: 4.4rem 3rem 3.2rem 3rem;
    overflow: hidden;
    border-bottom: 1px solid rgba(200, 210, 240, 0.12);
}
.hero-bleed .scene {
    position: absolute;
    inset: 0;
    opacity: 0;
    animation: crossfade 16s ease-in-out infinite;
}
.hero-bleed .scene-a {
    background:
        radial-gradient(circle at 18% 20%, rgba(58,90,190,0.55) 0%, transparent 55%),
        radial-gradient(circle at 82% 75%, rgba(212,175,55,0.18) 0%, transparent 50%),
        linear-gradient(160deg, #0b1330 0%, #050914 80%);
    animation-delay: 0s;
}
.hero-bleed .scene-b {
    background:
        radial-gradient(circle at 78% 15%, rgba(90,60,180,0.45) 0%, transparent 55%),
        radial-gradient(circle at 15% 80%, rgba(212,175,55,0.15) 0%, transparent 50%),
        linear-gradient(200deg, #0a1230 0%, #050914 80%);
    animation-delay: 8s;
}
@keyframes crossfade {
    0%   { opacity: 0; }
    8%   { opacity: 1; }
    42%  { opacity: 1; }
    50%  { opacity: 0; }
    100% { opacity: 0; }
}
.hero-bleed .grain {
    position: absolute; inset: 0;
    background-image: radial-gradient(1px 1px at 20% 30%, rgba(255,255,255,0.25) 0%, transparent 60%),
                       radial-gradient(1px 1px at 70% 60%, rgba(255,255,255,0.18) 0%, transparent 60%),
                       radial-gradient(1px 1px at 45% 80%, rgba(255,255,255,0.2) 0%, transparent 60%),
                       radial-gradient(1px 1px at 85% 20%, rgba(255,255,255,0.15) 0%, transparent 60%);
    opacity: 0.5;
}
.hero-content { position: relative; z-index: 1; }
.eyebrow {
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 0.32em;
    text-transform: uppercase;
    color: #b8a35f !important;
    margin-bottom: 1.1rem;
    animation: fadeIn 0.9s ease both;
}
.hero-headline {
    font-family: 'Fraunces', serif !important;
    font-weight: 500 !important;
    font-size: clamp(2.1rem, 4vw, 3.4rem) !important;
    line-height: 1.12 !important;
    color: #ffffff !important;
    max-width: 620px;
    margin-bottom: 1.1rem !important;
    animation: fadeUp 0.9s cubic-bezier(.22,1,.36,1) 0.1s both;
}
.hero-headline em { font-style: italic; color: #cdd7f2 !important; }
.hero-sub {
    font-family: 'Inter', sans-serif;
    color: #93a0c6 !important;
    font-size: 1.02rem;
    max-width: 460px;
    line-height: 1.6;
    animation: fadeUp 0.9s cubic-bezier(.22,1,.36,1) 0.25s both;
}
.hero-scroll {
    margin-top: 2.4rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #6c78a1 !important;
    display: flex; align-items: center; gap: 10px;
    animation: fadeIn 1.2s ease 0.5s both;
}
.hero-scroll::after {
    content: "";
    width: 28px; height: 1px;
    background: linear-gradient(90deg, #6c78a1, transparent);
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }

/* ---------------- SECTION HEADERS ---------------- */
h3 {
    font-family: 'Fraunces', serif !important;
    font-weight: 500 !important;
    font-style: normal;
    font-size: 1.5rem !important;
    color: #f2f4fc !important;
    margin-top: 3rem !important;
    margin-bottom: 0.4rem !important;
    letter-spacing: 0.01em;
}
h3::before {
    content: attr(data-step);
    display: block;
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: #6c78a1;
    margin-bottom: 0.5rem;
}
.section-wrap { animation: fadeUp 0.7s cubic-bezier(.22,1,.36,1) both; }
.section-wrap.s1 { animation-delay: 0.05s; }
.section-wrap.s2 { animation-delay: 0.12s; }
.section-wrap.s3 { animation-delay: 0.19s; }

.section-rule { height: 1px; background: rgba(180,195,230,0.1); margin-top: 2.6rem; }

/* ---------------- BUTTONS: thin, editorial, sweep-fill on hover ---------------- */
.stButton > button, .stDownloadButton > button {
    position: relative;
    background: transparent !important;
    color: #f2f4fc !important;
    border: 1px solid rgba(200, 210, 240, 0.45) !important;
    border-radius: 2px !important;
    padding: 0.75rem 2rem !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-size: 0.82rem;
    overflow: hidden;
    z-index: 0;
    transition: color 0.4s ease, border-color 0.4s ease !important;
    width: 100%;
}
.stButton > button::before, .stDownloadButton > button::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, #b8a35f, #8f7a3f);
    transform: scaleX(0);
    transform-origin: left;
    transition: transform 0.45s cubic-bezier(.22,1,.36,1);
    z-index: -1;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    color: #0a0e1f !important;
    border-color: #b8a35f !important;
}
.stButton > button:hover::before, .stDownloadButton > button:hover::before {
    transform: scaleX(1);
}

/* File uploader */
[data-testid="stFileUploadDropzone"] {
    background-color: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(180, 195, 230, 0.16) !important;
    border-radius: 4px !important;
    transition: border-color 0.3s ease, background 0.3s ease !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    background-color: rgba(184, 163, 95, 0.05) !important;
    border-color: rgba(184, 163, 95, 0.45) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: rgba(4, 7, 18, 0.95) !important;
    border-right: 1px solid rgba(180, 195, 230, 0.1);
}
[data-testid="stSidebar"] h3 {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #6c78a1 !important;
    margin-top: 1.4rem !important;
}
[data-testid="stSidebar"] h3::before { content: none; }

/* Inputs */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background-color: rgba(255,255,255,0.03) !important;
    color: #f0f2fb !important;
    border: 1px solid rgba(180, 195, 230, 0.2) !important;
    border-radius: 3px !important;
}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border: 1px solid rgba(184, 163, 95, 0.55) !important;
    box-shadow: 0 0 0 2px rgba(184, 163, 95, 0.1) !important;
}

/* Progress bar */
div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #445a9e, #b8a35f) !important;
}

.match-line { font-family: 'Inter', sans-serif; font-size: 0.9rem; padding: 3px 0; color: #a9b3d4 !important; }
</style>
""", unsafe_allow_html=True)


# --- SIDEBAR ---
st.sidebar.markdown("### Settings")
mode = st.sidebar.radio("Matching method", ["Gemini Vision AI", "Filename matching"])

api_key = ""
if mode == "Gemini Vision AI":
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.sidebar.success("Gemini connected")
    else:
        api_key = st.sidebar.text_input("Gemini API Key", type="password")

st.sidebar.markdown("### Background")
bg_video_file = st.sidebar.file_uploader(
    "Optional stadium video (.mp4)",
    type=["mp4"],
    help="Replaces the abstract hero backdrop with your own looping clip."
)
if bg_video_file is not None:
    video_b64 = base64.b64encode(bg_video_file.read()).decode()
    st.markdown(f"""
        <style>.hero-bleed .scene {{ display: none !important; }}</style>
        <div style="position: fixed; inset: 0; z-index: -100; overflow: hidden;">
            <video autoplay loop muted playsinline
                style="position:absolute; top:50%; left:50%; min-width:100%; min-height:100%;
                       transform: translate(-50%,-50%); object-fit: cover;
                       filter: brightness(0.28) saturate(1.05);">
              <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
            </video>
        </div>
        <div style="position: fixed; inset: 0; z-index: -99; pointer-events: none;
                    background: radial-gradient(circle at 50% 0%, rgba(16,32,79,0.3) 0%, rgba(3,5,15,0.8) 70%);">
        </div>
    """, unsafe_allow_html=True)


# --- HERO ---
st.markdown("""
    <div class="hero-bleed">
        <div class="scene scene-a"></div>
        <div class="scene scene-b"></div>
        <div class="grain"></div>
        <div class="hero-content">
            <div class="eyebrow">Matchday Preparation</div>
            <div class="hero-headline">Every face,<br><em>every number,</em><br>in seconds.</div>
            <div class="hero-sub">Upload a squad list and player photos — get every image renamed to its shirt number automatically.</div>
            <div class="hero-scroll">Begin below</div>
        </div>
    </div>
""", unsafe_allow_html=True)


# --- HELPER: NORMALIZE COLUMNS ---
def normalize_df(df):
    col_map = {}
    for col in df.columns:
        c_lower = str(col).strip().lower()
        if 'player' in c_lower or 'name' in c_lower:
            col_map[col] = 'Player'
        elif 'team' in c_lower or 'club' in c_lower:
            col_map[col] = 'Team'
        elif 'number' in c_lower or 'num' in c_lower or c_lower == '#':
            col_map[col] = 'Number'
    return df.rename(columns=col_map)


# --- HELPER: PARSE PASTED TEXT ---
def parse_pasted_text(text, default_team="AEK Athens"):
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    if not lines:
        return None

    if any('|' in line for line in lines):
        clean_lines = [l for l in lines if not all(c in '|- :' for c in l)]
        data = []
        for l in clean_lines:
            parts = [p.strip() for p in l.split('|') if p.strip()]
            if len(parts) >= 3:
                data.append({'Player': parts[0], 'Team': parts[1], 'Number': parts[2]})
            elif len(parts) == 2:
                data.append({'Player': parts[0], 'Team': default_team, 'Number': parts[1]})
        if data:
            df = pd.DataFrame(data)
            df = df[~df['Player'].str.lower().isin(['player', 'name', 'full name'])]
            return df

    try:
        df = pd.read_csv(io.StringIO(text), sep=None, engine='python')
        df = normalize_df(df)
        if 'Player' in df.columns and 'Number' in df.columns:
            if 'Team' not in df.columns:
                df['Team'] = default_team
            return df
    except Exception:
        pass

    rows = []
    for line in lines:
        parts = [p.strip() for p in re.split(r'[,;\t|]', line) if p.strip()]
        if len(parts) >= 3:
            rows.append({'Player': parts[0], 'Team': parts[1], 'Number': parts[2]})
        elif len(parts) == 2:
            rows.append({'Player': parts[0], 'Team': default_team, 'Number': parts[1]})
        else:
            m_start = re.match(r'^(\d+)\s+(.+)$', line)
            m_end = re.search(r'^(.*?)\s+(\d+)$', line)
            if m_start:
                rows.append({'Player': m_start.group(2).strip(), 'Team': default_team, 'Number': m_start.group(1).strip()})
            elif m_end:
                rows.append({'Player': m_end.group(1).strip(), 'Team': default_team, 'Number': m_end.group(2).strip()})

    return pd.DataFrame(rows) if rows else None


# --- STEP 1: SQUAD LIST ---
st.markdown('<div class="section-wrap s1">', unsafe_allow_html=True)
st.markdown('<h3 data-step="Step One">Squad List</h3>', unsafe_allow_html=True)
db_input_method = st.radio("Source", ["Upload file", "Paste text"], horizontal=True, label_visibility="collapsed")

df_db = None

if db_input_method == "Upload file":
    db_file = st.file_uploader("Excel (.xlsx) or CSV", type=["xlsx", "csv"])
    if db_file:
        try:
            df_raw = pd.read_excel(db_file) if db_file.name.endswith(".xlsx") else pd.read_csv(db_file)
            df_db = normalize_df(df_raw)
            st.success(f"Loaded {len(df_db)} players")
        except Exception as e:
            st.error(f"Error reading file: {e}")
else:
    default_team_input = st.text_input("Default team name (used if not specified in the text)", value="AEK Athens")
    pasted_text = st.text_area(
        "Paste player list",
        height=160,
        placeholder="Thomas Strakosha | AEK Athens | 1\nHarold Moukoudi | AEK Athens | 2\n\nor:\n1 Thomas Strakosha\n2 Harold Moukoudi"
    )
    if pasted_text:
        df_db = parse_pasted_text(pasted_text, default_team=default_team_input)
        if df_db is not None and not df_db.empty:
            st.success(f"Parsed {len(df_db)} players")
        else:
            st.error("Could not parse that list — check the format.")

if df_db is not None and not df_db.empty:
    st.dataframe(df_db.head(5), use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)

# --- STEP 2: IMAGES ---
st.markdown('<div class="section-wrap s2">', unsafe_allow_html=True)
st.markdown('<h3 data-step="Step Two">Player Photos</h3>', unsafe_allow_html=True)
st.caption("To keep nested subfolders, upload a .zip archive instead of loose files.")

uploaded_files = st.file_uploader(
    "Images or a .zip archive",
    type=["png", "jpg", "jpeg", "webp", "zip"],
    accept_multiple_files=True
)

images_to_process = {}

if uploaded_files:
    for f in uploaded_files:
        if f.name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(f, 'r') as z:
                    for file_info in z.infolist():
                        if not file_info.is_dir() and not file_info.filename.startswith('__MACOSX'):
                            if file_info.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                                images_to_process[file_info.filename] = z.read(file_info)
                st.success(f"Extracted {len(images_to_process)} images from `{f.name}`")
            except Exception as e:
                st.error(f"Error unzipping {f.name}: {e}")
        elif f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            images_to_process[f.name] = f.read()

    if images_to_process:
        st.caption(f"{len(images_to_process)} images ready.")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)


# --- GEMINI VISION ---
def identify_with_gemini(image_bytes, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(io.BytesIO(image_bytes))
    prompt = (
        "Identify the soccer player in this image. "
        "Return ONLY their full name and club team in this exact format: "
        "Player Name, Team Name."
    )
    response = model.generate_content([prompt, img])
    parts = response.text.strip().split(",")
    return parts[0].strip() if len(parts) > 0 else response.text.strip()


# --- STEP 3: RENAME ---
st.markdown('<div class="section-wrap s3">', unsafe_allow_html=True)
st.markdown('<h3 data-step="Step Three">Rename &amp; Download</h3>', unsafe_allow_html=True)

if st.button("Rename photos"):
    if df_db is None or df_db.empty:
        st.error("Load a squad list first.")
    elif not images_to_process:
        st.error("Upload at least one image or .zip file.")
    elif mode == "Gemini Vision AI" and not api_key:
        st.error("A Gemini API key is required for Vision AI mode.")
    else:
        zip_buffer = io.BytesIO()
        processed_count = 0

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
            progress_bar = st.progress(0)
            items = list(images_to_process.items())

            for idx, (img_path, img_bytes) in enumerate(items):
                filename = os.path.basename(img_path)
                folder_dir = os.path.dirname(img_path)
                original_ext = os.path.splitext(filename)[1]
                player_matched = None

                if mode == "Gemini Vision AI":
                    try:
                        detected_name = identify_with_gemini(img_bytes, api_key)
                        matches = df_db[df_db['Player'].str.contains(detected_name, case=False, na=False)]
                        if not matches.empty:
                            player_matched = matches.iloc[0]
                    except Exception as e:
                        st.warning(f"Could not identify {filename}: {e}")
                else:
                    for _, row in df_db.iterrows():
                        clean_player = str(row['Player']).lower()
                        if clean_player in filename.lower():
                            player_matched = row
                            break

                if player_matched is not None:
                    number = str(player_matched['Number'])
                    new_filename = f"{number}{original_ext}"
                    out_path = os.path.join(folder_dir, new_filename) if folder_dir else new_filename
                    zip_out.writestr(out_path, img_bytes)
                    st.markdown(f'<div class="match-line">✓ {img_path} → <b style="color:#e7ecfb !important;">{out_path}</b> ({player_matched["Player"]})</div>', unsafe_allow_html=True)
                    processed_count += 1
                else:
                    st.markdown(f'<div class="match-line" style="color:#8a6a6a !important;">— {img_path} → no match found</div>', unsafe_allow_html=True)

                progress_bar.progress((idx + 1) / len(items))

        if processed_count > 0:
            st.success(f"Renamed {processed_count} of {len(items)} images.")
            st.download_button(
                "Download renamed photos (.zip)",
                data=zip_buffer.getvalue(),
                file_name="Renamed_Player_Images.zip",
                mime="application/zip"
            )
st.markdown('</div>', unsafe_allow_html=True)
