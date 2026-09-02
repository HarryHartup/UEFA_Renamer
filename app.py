import streamlit as st
import pandas as pd
import os
import zipfile
import io
import re
import base64
from PIL import Image
import google.generativeai as genai

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="UCL Player Image Studio",
    page_icon="⭐",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ============================================================
# THEME / CSS — dark stadium-night palette, glass panels,
# glowing accents, drifting particle field, smooth motion.
# ============================================================
def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

    :root{
        --navy-0:#04050f;
        --navy-1:#0a0e27;
        --navy-2:#0d1230;
        --ucl-blue:#0a3bd0;
        --ucl-blue-2:#3a6bff;
        --ucl-purple:#5b2c91;
        --ucl-purple-2:#8b3fd6;
        --gold:#d4af37;
        --gold-soft:#f0d787;
        --ice:#eef2ff;
        --glass-border:rgba(255,255,255,0.09);
    }

    html, body, [class*="css"]{
        font-family: 'Inter', sans-serif;
    }

    /* ---------- KILL DEFAULT STREAMLIT CHROME ---------- */
    #MainMenu, header, footer {visibility:hidden;}
    .stApp{
        background: radial-gradient(circle at 20% 15%, #101a4a 0%, transparent 45%),
                    radial-gradient(circle at 85% 10%, #2a0d55 0%, transparent 40%),
                    radial-gradient(circle at 50% 90%, #0a1f4d 0%, transparent 50%),
                    linear-gradient(180deg, var(--navy-0) 0%, var(--navy-1) 45%, var(--navy-0) 100%);
        background-attachment: fixed;
        position: relative;
        overflow-x: hidden;
        isolation: isolate;
    }

    /* Drifting star / light-particle field (pure CSS, no assets) */
    .stApp::before{
        content:"";
        position:absolute; inset:0;
        z-index:0;
        pointer-events:none;
        background-image:
            radial-gradient(2px 2px at 10% 20%, rgba(255,255,255,0.55) 0%, transparent 60%),
            radial-gradient(1.5px 1.5px at 30% 70%, rgba(255,255,255,0.4) 0%, transparent 60%),
            radial-gradient(2px 2px at 60% 15%, rgba(212,175,55,0.6) 0%, transparent 60%),
            radial-gradient(1.5px 1.5px at 80% 55%, rgba(255,255,255,0.45) 0%, transparent 60%),
            radial-gradient(2px 2px at 45% 85%, rgba(139,63,214,0.55) 0%, transparent 60%),
            radial-gradient(1.5px 1.5px at 92% 80%, rgba(255,255,255,0.4) 0%, transparent 60%),
            radial-gradient(2px 2px at 15% 55%, rgba(58,107,255,0.55) 0%, transparent 60%);
        background-repeat: repeat;
        background-size: 100% 100%;
        animation: driftStars 40s linear infinite;
        opacity:0.9;
    }
    @keyframes driftStars{
        0%{ transform: translateY(0) translateX(0); }
        50%{ transform: translateY(-25px) translateX(15px); }
        100%{ transform: translateY(0) translateX(0); }
    }

    /* Glowing orbs floating slowly behind content */
    .orb{
        position:absolute; border-radius:50%;
        filter: blur(70px);
        z-index:0; pointer-events:none;
        opacity:0.35;
    }
    .orb-1{ width:420px; height:420px; top:-120px; left:-100px;
        background: radial-gradient(circle, var(--ucl-blue-2), transparent 70%);
        animation: floatA 22s ease-in-out infinite; }
    .orb-2{ width:380px; height:380px; bottom:-140px; right:-120px;
        background: radial-gradient(circle, var(--ucl-purple-2), transparent 70%);
        animation: floatB 26s ease-in-out infinite; }
    .orb-3{ width:260px; height:260px; top:40%; right:10%;
        background: radial-gradient(circle, var(--gold-soft), transparent 70%);
        opacity:0.18;
        animation: floatA 30s ease-in-out infinite reverse; }
    @keyframes floatA{
        0%,100%{ transform: translate(0,0) scale(1); }
        50%{ transform: translate(40px,30px) scale(1.08); }
    }
    @keyframes floatB{
        0%,100%{ transform: translate(0,0) scale(1); }
        50%{ transform: translate(-35px,-25px) scale(1.05); }
    }

    /* Background video layer (optional, user-supplied) */
    .bg-video-wrap{
        position:absolute; inset:0; z-index:0; overflow:hidden;
        pointer-events:none;
    }
    .bg-video-wrap video{
        position:absolute; top:50%; left:50%;
        min-width:100%; min-height:100%;
        width:auto; height:auto;
        transform: translate(-50%,-50%);
        object-fit:cover;
        filter: brightness(0.35) saturate(1.15);
    }
    .bg-video-tint{
        position:absolute; inset:0; z-index:0;
        pointer-events:none;
        background: linear-gradient(180deg, rgba(4,5,15,0.55) 0%, rgba(4,5,15,0.85) 75%, var(--navy-0) 100%);
    }

    .block-container{
        position:relative; z-index:10 !important;
        padding-top: 1.2rem;
        max-width: 900px;
    }
    section[data-testid="stSidebar"]{
        position:relative; z-index:10 !important;
    }

    /* ---------- HERO ---------- */
    .hero{
        text-align:center;
        padding: 1.4rem 1rem 1.6rem 1rem;
        margin-bottom: 1.6rem;
        animation: heroIn 1s cubic-bezier(.22,1,.36,1);
    }
    @keyframes heroIn{
        0%{ opacity:0; transform: translateY(-18px); }
        100%{ opacity:1; transform: translateY(0); }
    }
    .hero .eyebrow{
        font-family:'Rajdhani', sans-serif;
        letter-spacing: 0.45em;
        font-size: 0.72rem;
        font-weight:600;
        color: var(--gold-soft);
        text-transform: uppercase;
        margin-bottom: 0.6rem;
        display:flex; align-items:center; justify-content:center; gap:10px;
    }
    .hero .eyebrow::before, .hero .eyebrow::after{
        content:""; height:1px; width:34px;
        background: linear-gradient(90deg, transparent, var(--gold-soft));
    }
    .hero .eyebrow::after{ background: linear-gradient(90deg, var(--gold-soft), transparent); }

    .hero h1{
        font-family:'Orbitron', sans-serif;
        font-weight:900;
        font-size: clamp(2rem, 6vw, 3.1rem);
        line-height:1.05;
        margin: 0;
        letter-spacing: 0.01em;
        background: linear-gradient(100deg, #ffffff 10%, #bcd0ff 35%, var(--gold-soft) 55%, #ffffff 80%);
        background-size: 220% auto;
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 6s linear infinite;
        text-shadow: 0 0 45px rgba(58,107,255,0.25);
    }
    @keyframes shimmer{
        0%{ background-position: 0% center; }
        100%{ background-position: 220% center; }
    }
    .hero p.sub{
        font-family:'Rajdhani', sans-serif;
        color: #9fb1e0;
        font-size: 1.02rem;
        margin-top: 0.55rem;
        font-weight:500;
        letter-spacing:0.02em;
    }
    .hero .pitch-line{
        width: 120px; height: 3px; margin: 1.1rem auto 0 auto;
        background: linear-gradient(90deg, transparent, var(--ucl-blue-2), var(--gold-soft), var(--ucl-purple-2), transparent);
        border-radius: 3px;
        box-shadow: 0 0 18px rgba(58,107,255,0.6);
    }

    /* ---------- STEP BADGE + GLASS PANELS ---------- */
    .step-head{
        display:flex; align-items:center; gap:0.85rem;
        margin: 1.6rem 0 0.7rem 0;
    }
    .step-badge{
        font-family:'Orbitron', sans-serif;
        font-weight:700;
        font-size: 0.95rem;
        width: 38px; height:38px;
        min-width:38px;
        border-radius: 50%;
        display:flex; align-items:center; justify-content:center;
        color:#0a0e27;
        background: linear-gradient(135deg, var(--gold-soft), var(--gold));
        box-shadow: 0 0 0 3px rgba(212,175,55,0.15), 0 6px 18px rgba(212,175,55,0.35);
    }
    .step-title{
        font-family:'Rajdhani', sans-serif;
        font-weight:700;
        font-size: 1.28rem;
        color: var(--ice);
        letter-spacing:0.01em;
    }
    .step-title span{
        display:block;
        font-family:'Inter', sans-serif;
        font-weight:400;
        font-size:0.82rem;
        color:#8494c4;
        letter-spacing:0.02em;
    }

    .glass{
        background: linear-gradient(160deg, rgba(255,255,255,0.055), rgba(255,255,255,0.015));
        border: 1px solid var(--glass-border);
        border-radius: 18px;
        padding: 1.3rem 1.4rem 1.1rem 1.4rem;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        margin-bottom: 0.4rem;
        transition: box-shadow 0.4s ease, transform 0.4s ease, border-color 0.4s ease;
        animation: panelIn 0.7s cubic-bezier(.22,1,.36,1);
    }
    .glass:hover{
        border-color: rgba(58,107,255,0.35);
        box-shadow: 0 8px 40px rgba(58,107,255,0.18);
    }
    @keyframes panelIn{
        0%{ opacity:0; transform: translateY(14px); }
        100%{ opacity:1; transform: translateY(0); }
    }

    /* ---------- WIDGET RESKIN ---------- */

    /* Text inputs / text areas / selects */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div{
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        color: var(--ice) !important;
        border-radius: 10px !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput input:focus, .stTextArea textarea:focus{
        border-color: var(--ucl-blue-2) !important;
        box-shadow: 0 0 0 3px rgba(58,107,255,0.18) !important;
    }

    /* Radio */
    div[role="radiogroup"] label{
        font-family:'Rajdhani', sans-serif;
        font-weight:600;
        color: #cdd8f5 !important;
    }

    /* File uploader dropzone */
    [data-testid="stFileUploaderDropzone"]{
        background: repeating-linear-gradient(135deg, rgba(255,255,255,0.02) 0 10px, rgba(255,255,255,0.045) 10px 20px) !important;
        border: 1.5px dashed rgba(139,63,214,0.5) !important;
        border-radius: 14px !important;
        transition: border-color 0.3s ease, background 0.3s ease;
    }
    [data-testid="stFileUploaderDropzone"]:hover{
        border-color: var(--gold-soft) !important;
    }

    /* Buttons */
    .stButton > button, .stDownloadButton > button{
        font-family:'Rajdhani', sans-serif;
        font-weight:700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        font-size: 0.95rem;
        color: #04050f !important;
        background: linear-gradient(120deg, var(--gold-soft), var(--gold) 55%, var(--gold-soft)) !important;
        background-size: 220% auto;
        border: none !important;
        border-radius: 999px !important;
        padding: 0.7rem 1.6rem !important;
        box-shadow: 0 8px 24px rgba(212,175,55,0.3), 0 0 0 1px rgba(212,175,55,0.25) inset;
        transition: transform 0.25s ease, box-shadow 0.25s ease, background-position 0.6s ease;
        width: 100%;
    }
    .stButton > button:hover, .stDownloadButton > button:hover{
        transform: translateY(-2px) scale(1.01);
        background-position: right center;
        box-shadow: 0 12px 30px rgba(212,175,55,0.45), 0 0 0 1px rgba(212,175,55,0.4) inset;
        color:#04050f !important;
    }
    .stButton > button:active{ transform: translateY(0) scale(0.99); }

    /* Progress bar */
    div[data-testid="stProgress"] > div > div{
        background: linear-gradient(90deg, var(--ucl-blue-2), var(--ucl-purple-2), var(--gold-soft)) !important;
        box-shadow: 0 0 12px rgba(58,107,255,0.6);
    }

    /* Success / warning / error / info boxes */
    div[data-testid="stAlert"]{
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        backdrop-filter: blur(8px);
        animation: alertIn 0.4s ease;
    }
    @keyframes alertIn{
        0%{ opacity:0; transform: translateX(-8px); }
        100%{ opacity:1; transform: translateX(0); }
    }

    /* Dataframe */
    [data-testid="stDataFrame"]{
        border-radius: 12px !important;
        overflow:hidden;
        border: 1px solid var(--glass-border) !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"]{
        background: linear-gradient(180deg, #080b22 0%, #0a0e27 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3{
        font-family:'Orbitron', sans-serif !important;
        color: var(--gold-soft) !important;
        font-size: 1.05rem !important;
    }

    /* Divider glow */
    .glow-divider{
        height:1px; width:100%; margin: 1.6rem 0 1.2rem 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
    }

    /* Footer */
    .ucl-footer{
        text-align:center;
        margin-top: 2.4rem;
        padding: 1.4rem 0 2rem 0;
        font-family:'Rajdhani', sans-serif;
        color: #5a6796;
        font-size: 0.82rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .ucl-footer b{ color: var(--gold-soft); }

    /* Match-result style row for renamed files */
    .result-row{
        display:flex; align-items:center; gap:0.7rem;
        padding: 0.5rem 0.7rem;
        border-radius: 10px;
        margin-bottom: 0.35rem;
        font-family:'Rajdhani', sans-serif;
        font-weight:600;
        font-size: 0.92rem;
        animation: rowIn 0.4s ease;
        border-left: 3px solid transparent;
    }
    @keyframes rowIn{
        0%{ opacity:0; transform: translateX(-10px); }
        100%{ opacity:1; transform: translateX(0); }
    }
    .result-row.ok{
        background: rgba(58,107,255,0.08);
        border-left-color: var(--ucl-blue-2);
        color:#d6e0ff;
    }
    .result-row.fail{
        background: rgba(214,58,58,0.07);
        border-left-color: #d63a3a;
        color:#f2cfcf;
    }
    .result-row .tag{
        font-family:'Orbitron', sans-serif;
        font-size:0.65rem;
        padding: 3px 8px;
        border-radius: 999px;
        letter-spacing:0.05em;
    }
    .result-row.ok .tag{ background: rgba(58,107,255,0.25); color:#bcd0ff; }
    .result-row.fail .tag{ background: rgba(214,58,58,0.22); color:#f2b8b8; }
    </style>
    """, unsafe_allow_html=True)


def inject_background_video(video_bytes: bytes):
    """Render an autoplay/looping/muted video as a full-bleed background layer."""
    b64 = base64.b64encode(video_bytes).decode()
    st.markdown(f"""
        <div class="bg-video-wrap">
            <video autoplay loop muted playsinline>
                <source src="data:video/mp4;base64,{b64}" type="video/mp4">
            </video>
        </div>
        <div class="bg-video-tint"></div>
    """, unsafe_allow_html=True)


def inject_ambient_orbs():
    st.markdown("""
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
    """, unsafe_allow_html=True)


def step_header(number: str, title: str, subtitle: str):
    st.markdown(f"""
        <div class="step-head">
            <div class="step-badge">{number}</div>
            <div class="step-title">{title}<span>{subtitle}</span></div>
        </div>
    """, unsafe_allow_html=True)


inject_css()

# ============================================================
# SIDEBAR — SETTINGS
# ============================================================
st.sidebar.markdown("### ⚙️ Match Settings")
mode = st.sidebar.radio(
    "Recognition Mode",
    ["Gemini Vision AI (Recognize Face/Jersey)", "Filename Matching (No API Key)"]
)

api_key = ""
if mode == "Gemini Vision AI (Recognize Face/Jersey)":
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.sidebar.success("✅ Gemini API Key loaded from Secrets!")
    else:
        api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Get a free key at aistudio.google.com")
        if not api_key:
            st.sidebar.warning("⚠️ Enter a Google Gemini API key to use Vision AI.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎬 Stadium Atmosphere")
bg_video_file = st.sidebar.file_uploader(
    "Background hype video (optional, .mp4)",
    type=["mp4"],
    help="Drop in your own Champions League–style hype clip and it'll loop behind the whole app, dimmed for readability."
)

# ============================================================
# BACKGROUND LAYERS
# ============================================================
if bg_video_file is not None:
    inject_background_video(bg_video_file.read())
else:
    inject_ambient_orbs()

# ============================================================
# HERO
# ============================================================
st.markdown("""
    <div class="hero">
        <div class="eyebrow">Est. for Matchday Squads</div>
        <h1>PLAYER IMAGE STUDIO</h1>
        <p class="sub">Auto-match faces to shirt numbers. Rename entire squads in seconds.</p>
        <div class="pitch-line"></div>
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

    # Option 1: Markdown Table Parsing (| Player | Team | Number |)
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

    # Option 2: Try CSV/TSV
    try:
        df = pd.read_csv(io.StringIO(text), sep=None, engine='python')
        df = normalize_df(df)
        if 'Player' in df.columns and 'Number' in df.columns:
            if 'Team' not in df.columns:
                df['Team'] = default_team
            return df
    except Exception:
        pass

    # Option 3: Fallback Line-by-Line Regex
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


# ============================================================
# STEP 1 — SQUAD DATABASE
# ============================================================
step_header("01", "Squad Database", "Load your roster of players, teams & numbers")
st.markdown('<div class="glass">', unsafe_allow_html=True)

db_input_method = st.radio("Input Method", ["Upload Excel/CSV File", "Paste Player List Text"], horizontal=True)

df_db = None

if db_input_method == "Upload Excel/CSV File":
    db_file = st.file_uploader("Upload Excel (.xlsx) or CSV", type=["xlsx", "csv"])
    if db_file:
        try:
            df_raw = pd.read_excel(db_file) if db_file.name.endswith(".xlsx") else pd.read_csv(db_file)
            df_db = normalize_df(df_raw)
            st.success(f"✅ Loaded {len(df_db)} players from file!")
        except Exception as e:
            st.error(f"Error reading file: {e}")

else:
    default_team_input = st.text_input("Default Team Name (if not specified in text)", value="AEK Athens")
    pasted_text = st.text_area(
        "Paste Player List Here",
        height=180,
        placeholder="Example:\nThomas Strakosha | AEK Athens | 1\nHarold Moukoudi | AEK Athens | 2\n\nOR:\n1 Thomas Strakosha\n2 Harold Moukoudi"
    )
    if pasted_text:
        df_db = parse_pasted_text(pasted_text, default_team=default_team_input)
        if df_db is not None and not df_db.empty:
            st.success(f"✅ Parsed {len(df_db)} players from pasted text!")
        else:
            st.error("Could not parse player list. Please check format.")

if df_db is not None and not df_db.empty:
    st.dataframe(df_db.head(5), use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# STEP 2 — UPLOAD IMAGES
# ============================================================
step_header("02", "Player Images", "Drop in photos, folders, or a full .zip archive")
st.markdown('<div class="glass">', unsafe_allow_html=True)

st.info("💡 **Subfolder Tip:** To preserve and search nested subfolders, upload a **`.zip` archive** containing your folders!")

uploaded_files = st.file_uploader(
    "Drag & drop image files OR a .zip archive containing subfolders",
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
                st.success(f"✅ Extracted {len(images_to_process)} images from subfolders inside `{f.name}`")
            except Exception as e:
                st.error(f"Error unzipping {f.name}: {e}")
        elif f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            images_to_process[f.name] = f.read()

    if images_to_process:
        st.markdown(f"**Total Images Ready for Processing:** `{len(images_to_process)}`")

st.markdown('</div>', unsafe_allow_html=True)


# --- HELPER: GEMINI VISION ---
def identify_with_gemini(image_bytes, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(io.BytesIO(image_bytes))

    prompt = (
        "Identify the soccer player in this image. "
        "Return ONLY their full name and club team in this exact format: "
        "Player Name, Team Name. Example: Luka Jović, AEK Athens"
    )

    response = model.generate_content([prompt, img])
    text = response.text.strip()
    parts = text.split(",")
    return parts[0].strip() if len(parts) > 0 else text


# ============================================================
# STEP 3 — PROCESS & RENAME
# ============================================================
step_header("03", "Kickoff", "Run the match & download your renamed squad")
st.markdown('<div class="glass">', unsafe_allow_html=True)

run_clicked = st.button("⚡ Process & Rename Images")
st.markdown('</div>', unsafe_allow_html=True)

if run_clicked:
    if df_db is None or df_db.empty:
        st.error("Please load or paste a database first.")
    elif not images_to_process:
        st.error("Please upload at least one image or zip file.")
    elif mode == "Gemini Vision AI (Recognize Face/Jersey)" and not api_key:
        st.error("Gemini API key is required for Vision AI mode.")
    else:
        st.markdown('<div class="glass">', unsafe_allow_html=True)

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

                if mode == "Gemini Vision AI (Recognize Face/Jersey)":
                    try:
                        detected_name = identify_with_gemini(img_bytes, api_key)
                        matches = df_db[df_db['Player'].str.contains(detected_name, case=False, na=False)]
                        if not matches.empty:
                            player_matched = matches.iloc[0]
                    except Exception as e:
                        st.warning(f"Failed AI detection for {filename}: {e}")
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
                    st.markdown(
                        f'<div class="result-row ok"><span class="tag">MATCH</span>'
                        f'<b>{img_path}</b>&nbsp;→&nbsp;<code>{out_path}</code>&nbsp;'
                        f'({player_matched["Player"]})</div>',
                        unsafe_allow_html=True
                    )
                    processed_count += 1
                else:
                    st.markdown(
                        f'<div class="result-row fail"><span class="tag">NO MATCH</span>'
                        f'<b>{img_path}</b>&nbsp;→&nbsp;not found in database</div>',
                        unsafe_allow_html=True
                    )

                progress_bar.progress((idx + 1) / len(items))

        if processed_count > 0:
            st.success(f"🏆 Finished! Successfully renamed {processed_count} images.")
            st.download_button(
                label="📦 Download Renamed Images (.zip)",
                data=zip_buffer.getvalue(),
                file_name="Renamed_Player_Images.zip",
                mime="application/zip"
            )

        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
st.markdown("""
    <div class="ucl-footer">
        Built for <b>Matchday</b> · Player Image Studio
    </div>
""", unsafe_allow_html=True)
