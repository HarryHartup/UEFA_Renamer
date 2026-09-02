import io
import os
import re
import unicodedata
import zipfile
from PIL import Image
import google.generativeai as genai
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="HEI Image Renamer 6000",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLOBAL STYLES & ANIMATED BACKDROP ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Syne:wght@700;800;900&display=swap');

:root {
    --bg-main: #020617;
    --bg-card: rgba(8, 15, 35, 0.85);
    --border-color: rgba(0, 240, 255, 0.35);
    --text-primary: #F8FAFC;
    --accent-cyan: #00F0FF;
    --accent-volt: #E2F163;
}

#MainMenu, footer { visibility: hidden; }

html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: var(--bg-main) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-primary) !important;
}

.stApp::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: -1;
    background: 
        radial-gradient(circle at 15% 20%, rgba(0, 240, 255, 0.18) 0%, transparent 45%),
        radial-gradient(circle at 85% 80%, rgba(0, 20, 137, 0.45) 0%, transparent 50%),
        radial-gradient(circle at 50% 50%, rgba(226, 241, 99, 0.08) 0%, transparent 60%),
        radial-gradient(circle at 80% 10%, rgba(0, 102, 255, 0.25) 0%, transparent 40%);
    background-size: 180% 180%;
    animation: uclMeshMove 14s ease-in-out infinite alternate;
}

@keyframes uclMeshMove {
    0% { background-position: 0% 0%; }
    50% { background-position: 100% 100%; }
    100% { background-position: 0% 100%; }
}

.block-container {
    max-width: 1050px !important;
    padding-top: 2.5rem !important;
    padding-bottom: 5rem !important;
    background: var(--bg-card) !important;
    backdrop-filter: blur(25px) !important;
    -webkit-backdrop-filter: blur(25px) !important;
    border: 1px solid var(--border-color);
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.85);
    margin-top: 2rem !important;
    margin-bottom: 2rem !important;
}

.editorial-header {
    border-bottom: 2px solid var(--accent-cyan);
    padding-bottom: 1.5rem;
    margin-bottom: 2.5rem;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}

.editorial-title {
    font-family: 'Syne', sans-serif !important;
    font-weight: 900 !important;
    font-size: 3.2rem !important;
    letter-spacing: -0.03em;
    text-transform: uppercase;
    color: #FFFFFF;
    margin: 0;
    line-height: 0.95;
    text-shadow: 0 0 25px rgba(0, 240, 255, 0.5);
}

.editorial-subtitle {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.8rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--accent-volt);
    margin-top: 0.6rem;
    font-weight: 700;
}

.brand-badge {
    border: 1px solid var(--accent-cyan);
    padding: 0.4rem 0.8rem;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent-cyan);
    background: rgba(0, 240, 255, 0.12);
    font-weight: 700;
}

.stRadio > div {
    background: rgba(11, 19, 43, 0.9) !important;
    border: 1px solid var(--border-color) !important;
    padding: 0.5rem !important;
}

.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: rgba(11, 19, 43, 0.9) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    padding: 0.75rem !important;
}

[data-testid="stFileUploadDropzone"] {
    background: rgba(11, 19, 43, 0.9) !important;
    border: 1px dashed rgba(0, 240, 255, 0.4) !important;
}

.stButton > button {
    background: var(--accent-cyan) !important;
    color: #000000 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border: none !important;
    padding: 1rem 2rem !important;
    box-shadow: 4px 4px 0px #000000, 4px 4px 0px 2px var(--accent-volt) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    width: 100% !important;
}

.stButton > button:hover {
    transform: translate(-2px, -2px) !important;
    box-shadow: 6px 6px 0px #000000, 6px 6px 0px 2px var(--accent-volt) !important;
}

[data-testid="stSidebar"] {
    background-color: rgba(8, 15, 35, 0.95) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid var(--border-color) !important;
    padding-top: 2rem !important;
}

[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}
</style>

<div class="editorial-header">
    <div>
        <div class="editorial-title">UCL SQUAD RENAME</div>
        <div class="editorial-subtitle">// Players to JSON thingy ma doodad</div>
    </div>
    <div class="brand-badge">HEI Image Renamer 6000</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR PANEL CONTROL ---
with st.sidebar:
    st.markdown("### ⚙️ SYSTEM SETTINGS")
    enable_ai_pass = st.checkbox("Enable Pass 2 (Gemini Vision AI Fallback)", value=True)

    api_key = ""
    if enable_ai_pass:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✓ Milking your API Keys")
        else:
            api_key = st.text_input("Gemini API Key", type="password")
            if not api_key:
                st.warning("⚠️ Enter a Google Gemini API key for Pass 2.")

# --- STRING NORMALIZATION ENGINE ---
def clean_text(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('_', ' ').replace('-', ' ')
    return ' '.join(text.split()).lower()

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
    df = df.rename(columns=col_map)
    if 'Team' not in df.columns:
        df['Team'] = 'Unknown Club'
    return df

def parse_pasted_text(text, default_team="AEK Athens"):
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    if not lines:
        return None

    rows = []
    for line in lines:
        parts = [p.strip() for p in line.split('|') if p.strip()]
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

    df = pd.DataFrame(rows) if rows else None
    if df is not None:
        df = df[~df['Player'].str.lower().isin(['player', 'name', 'full name'])]
    return df

# --- SECTION 1: SQUAD DATA ---
st.markdown("##### [01] ROSTER DATABASE SOURCE")
db_input_method = st.radio("Input Mode", ["Upload File (Excel/CSV/JSON)", "Paste Roster Text"], horizontal=True)

df_db = None

if db_input_method == "Upload File (Excel/CSV/JSON)":
    db_file = st.file_uploader("Upload Excel (.xlsx), CSV, or JSON containing squad rosters", type=["xlsx", "csv", "json"])
    if db_file:
        try:
            if db_file.name.endswith(".xlsx"):
                df_raw = pd.read_excel(db_file)
            elif db_file.name.endswith(".json"):
                df_raw = pd.read_json(db_file)
            else:
                df_raw = pd.read_csv(db_file)
            df_db = normalize_df(df_raw)
            st.success(f"✓ Master Roster Active: {len(df_db)} Athletes across {df_db['Team'].nunique()} Clubs")
        except Exception as e:
            st.error(f"Error parsing database file: {e}")
else:
    default_team_input = st.text_input("Fallback Club Name", value="AEK Athens")
    pasted_text = st.text_area(
        "Paste Roster Content",
        height=160,
        placeholder="Thomas Strakosha | AEK Athens | 1\nKasper Schmeichel | Celtic | 1"
    )
    if pasted_text:
        df_db = parse_pasted_text(pasted_text, default_team=default_team_input)
        if df_db is not None and not df_db.empty:
            st.success(f"✓ Parsed {len(df_db)} Athletes across {df_db['Team'].nunique()} Clubs!")

if df_db is not None and not df_db.empty:
    st.dataframe(df_db.head(5), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SECTION 2: ASSETS & SUBFOLDERS ---
st.markdown("##### [02] MEDIA ASSETS & FOLDERS")
uploaded_files = st.file_uploader(
    "Drop Individual Images OR a .ZIP Folder",
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
                st.success(f"Extracted {len(images_to_process)} assets from zip archive: {f.name}")
            except Exception as e:
                st.error(f"Error reading zip structure: {e}")
        elif f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            images_to_process[f.name] = f.read()

    if images_to_process:
        st.write(f"Total Processing Queue: **{len(images_to_process)}** media files ready.")

# --- VISION AI RECOGNITION (PASS 2 ONLY) ---
def identify_with_gemini(image_bytes, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    img = Image.open(io.BytesIO(image_bytes))
    prompt = (
        "Identify the soccer player and their club team in this image. "
        "Return ONLY their full name and club team in this exact format: "
        "Player Name, Team Name."
    )
    response = model.generate_content([prompt, img])
    parts = response.text.strip().split(",")
    return parts[0].strip() if len(parts) > 0 else response.text.strip()

# --- SECTION 3: SEQUENTIAL TWO-PASS EXECUTION ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("EXECUTE TWO-PASS BATCH PROCESS"):
    if df_db is None or df_db.empty:
        st.error("No valid roster loaded.")
    elif not images_to_process:
        st.error("No image assets provided.")
    elif enable_ai_pass and not api_key:
        st.error("Gemini API Key required when Pass 2 is enabled.")
    else:
        zip_buffer = io.BytesIO()
        matched_db_indices = set()
        unmatched_images = []
        
        pass1_matched = {}
        pass2_queue = {}

        items = list(images_to_process.items())
        total_items = len(items)

        st.markdown("#### ⚡ PASS 1: FAST LOCAL FILENAME MATCHING")
        p1_bar = st.progress(0)

        # PASS 1: LOCAL ACCENT-INSENSITIVE MATCHING
        for idx, (img_path, img_bytes) in enumerate(items):
            filename = os.path.basename(img_path)
            folder_dir = os.path.dirname(img_path)
            cleaned_filename = clean_text(filename)
            cleaned_folder = clean_text(folder_dir)
            player_matched = None
            matched_row_idx = None

            for db_idx, row in df_db.iterrows():
                clean_db_player = clean_text(row['Player'])
                clean_db_team = clean_text(row['Team'])
                player_parts = clean_db_player.split()
                last_name = player_parts[-1] if player_parts else clean_db_player

                if clean_db_player in cleaned_filename or (len(last_name) > 3 and last_name in cleaned_filename):
                    if cleaned_folder and clean_db_team and clean_db_team in cleaned_folder:
                        player_matched = row
                        matched_row_idx = db_idx
                        break
                    elif not player_matched:
                        player_matched = row
                        matched_row_idx = db_idx

            if player_matched is not None:
                pass1_matched[img_path] = (player_matched, img_bytes)
                matched_db_indices.add(matched_row_idx)
                st.write(f"⚡ **[Pass 1 Match]** `{img_path}` → Renamed to `{player_matched['Number']}` ({player_matched['Player']})")
            else:
                pass2_queue[img_path] = img_bytes

            p1_bar.progress((idx + 1) / total_items)

        st.success(f"Pass 1 Complete! Resolved {len(pass1_matched)} / {total_items} images locally without API calls.")

        # PASS 2: GEMINI VISION AI FALLBACK
        if pass2_queue and enable_ai_pass:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"#### 🧠 PASS 2: GEMINI AI VISION RECOGNITION ({len(pass2_queue)} Remaining)")
            p2_bar = st.progress(0)
            pass2_items = list(pass2_queue.items())

            for idx, (img_path, img_bytes) in enumerate(pass2_items):
                filename = os.path.basename(img_path)
                player_matched = None
                matched_row_idx = None

                try:
                    detected_name = identify_with_gemini(img_bytes, api_key)
                    cleaned_detected = clean_text(detected_name)

                    for db_idx, row in df_db.iterrows():
                        clean_db_player = clean_text(row['Player'])
                        if clean_db_player in cleaned_detected or cleaned_detected in clean_db_player:
                            player_matched = row
                            matched_row_idx = db_idx
                            break
                except Exception as e:
                    st.warning(f"Pass 2 AI bypass on {filename}: {e}")

                if player_matched is not None:
                    pass1_matched[img_path] = (player_matched, img_bytes)
                    matched_db_indices.add(matched_row_idx)
                    st.write(f"🧠 **[Pass 2 Match]** `{img_path}` → Renamed to `{player_matched['Number']}` ({player_matched['Player']})")
                else:
                    st.write(f"✕ `{img_path}` → Unmatched after both passes.")
                    unmatched_images.append(img_path)

                p2_bar.progress((idx + 1) / len(pass2_items))

        elif pass2_queue and not enable_ai_pass:
            for img_path in pass2_queue.keys():
                unmatched_images.append(img_path)

        # WRITE OUTPUT ZIP & RENDER CONSOLES
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
            for img_path, (player_row, img_bytes) in pass1_matched.items():
                folder_dir = os.path.dirname(img_path)
                original_ext = os.path.splitext(os.path.basename(img_path))[1]
                number = str(player_row['Number'])
                new_filename = f"{number}{original_ext}"
                out_path = os.path.join(folder_dir, new_filename) if folder_dir else new_filename
                zip_out.writestr(out_path, img_bytes)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📋 RESOLUTION CONSOLES (CLICK TO COPY)")
        
        unmatched_db = df_db[~df_db.index.isin(matched_db_indices)]
        c_col1, c_col2 = st.columns(2)

        with c_col1:
            st.markdown(f"##### 🔴 Unmatched Images Console ({len(unmatched_images)})")
            if unmatched_images:
                st.code("\n".join(unmatched_images), language="text")
            else:
                st.success("All images successfully matched!")

        with c_col2:
            st.markdown(f"##### 🟡 Leftover Roster Console ({len(unmatched_db)})")
            if not unmatched_db.empty:
                console_roster_lines = [
                    f"{row['Player']} | {row['Team']} | {row['Number']}"
                    for _, row in unmatched_db.iterrows()
                ]
                st.code("\n".join(console_roster_lines), language="text")
            else:
                st.success("All roster players received image assets!")

        if len(pass1_matched) > 0:
            st.download_button(
                label="📦 DOWNLOAD RENAMED ZIP ARCHIVE",
                data=zip_buffer.getvalue(),
                file_name="UCL_Renamed_Assets.zip",
                mime="application/zip"
            )
