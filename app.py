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
    page_title="UCL SQUAD RENAME ENGINE",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLOBAL STYLES & ANIMATED BACKGROUND ---
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

/* Hide default Streamlit chrome */
#MainMenu, footer { visibility: hidden; }

/* Global Background Lock */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: var(--bg-main) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Animated Dynamic Gradient Mesh Backdrop */
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

/* Glassmorphic Card Container */
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

/* Header Typography */
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

/* Form Inputs & Upload Zone */
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

/* Action Button */
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

/* Sidebar Custom Styling */
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

<!-- EDITORIAL HEADER -->
<div class="editorial-header">
    <div>
        <div class="editorial-title">UCL SQUAD RENAME</div>
        <div class="editorial-subtitle">// ASSET MANAGEMENT & VISION RECOGNITION ENGINE</div>
    </div>
    <div class="brand-badge">UEFA OFFICIAL SPECTRA</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR PANEL CONTROL ---
with st.sidebar:
    st.markdown("### ⚙️ SYSTEM SETTINGS")
    mode = st.radio(
        "RECOGNITION ENGINE", 
        ["Gemini Vision AI", "Filename Matching"]
    )

    api_key = ""
    if mode == "Gemini Vision AI":
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✓ Secure AI Uplink Active")
        else:
            api_key = st.text_input("Gemini API Key", type="password")
            if not api_key:
                st.warning("⚠️ Enter a Google Gemini API key.")

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
    return df.rename(columns=col_map)

def parse_pasted_text(text, default_team="AEK Athens"):
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    if not lines:
        return None

    rows = []
    if any('|' in line for line in lines):
        clean_lines = [l for l in lines if not all(c in '|- :' for c in l)]
        for l in clean_lines:
            parts = [p.strip() for p in l.split('|') if p.strip()]
            if len(parts) >= 3:
                rows.append({'Player': parts[0], 'Team': parts[1], 'Number': parts[2]})
            elif len(parts) == 2:
                rows.append({'Player': parts[0], 'Team': default_team, 'Number': parts[1]})
        if rows:
            df = pd.DataFrame(rows)
            df = df[~df['Player'].str.lower().isin(['player', 'name', 'full name'])]
            return df
    else:
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

# --- SECTION 1: SQUAD DATA ---
st.markdown("##### [01] SQUAD DATABASE & ROSTER SOURCE")
db_input_method = st.radio("Input Mode", ["Upload File", "Paste Roster Text"], horizontal=True)

df_db = None

if db_input_method == "Upload File":
    db_file = st.file_uploader("Upload Excel (.xlsx), CSV, or JSON File", type=["xlsx", "csv", "json"])
    if db_file:
        try:
            if db_file.name.endswith(".xlsx"):
                df_raw = pd.read_excel(db_file)
            elif db_file.name.endswith(".json"):
                df_raw = pd.read_json(db_file)
            else:
                df_raw = pd.read_csv(db_file)
            df_db = normalize_df(df_raw)
            st.success(f"✓ Roster Active: {len(df_db)} Records")
        except Exception as e:
            st.error(f"Error parsing database file: {e}")
else:
    default_team_input = st.text_input("Default Club Name", value="AEK Athens")
    pasted_text = st.text_area(
        "Paste Roster Content",
        height=140,
        placeholder="Thomas Strakosha | AEK Athens | 1\nHarold Moukoudi | AEK Athens | 2"
    )
    if pasted_text:
        df_db = parse_pasted_text(pasted_text, default_team=default_team_input)
        if df_db is not None and not df_db.empty:
            st.success(f"✓ Roster Parsed: {len(df_db)} Athletes")

if df_db is not None and not df_db.empty:
    st.dataframe(df_db.head(4), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SECTION 2: ASSETS & SUBFOLDERS ---
st.markdown("##### [02] MEDIA ASSETS & ARCHIVES")
uploaded_files = st.file_uploader(
    "Drop Individual Images OR a .ZIP Folder (Preserves Subfolder Trees)",
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
                st.success(f"Extracted {len(images_to_process)} assets from subfolder archive: {f.name}")
            except Exception as e:
                st.error(f"Error reading zip structure: {e}")
        elif f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            images_to_process[f.name] = f.read()

    if images_to_process:
        st.write(f"Total Queue: **{len(images_to_process)}** media files ready.")

# --- VISION AI RECOGNITION ---
def identify_with_gemini(image_bytes, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    img = Image.open(io.BytesIO(image_bytes))
    prompt = (
        "Identify the soccer player in this image. "
        "Return ONLY their full name and club team in this exact format: "
        "Player Name, Team Name."
    )
    response = model.generate_content([prompt, img])
    parts = response.text.strip().split(",")
    return parts[0].strip() if len(parts) > 0 else response.text.strip()

# --- SECTION 3: ACCENT-INSENSITIVE EXECUTION & LEFTOVER AUDIT ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("EXECUTE BATCH PROCESS"):
    if df_db is None or df_db.empty:
        st.error("No valid roster loaded.")
    elif not images_to_process:
        st.error("No image assets provided.")
    elif mode == "Gemini Vision AI" and not api_key:
        st.error("Gemini API Key required.")
    else:
        zip_buffer = io.BytesIO()
        processed_count = 0
        
        # Tracking sets for audit logs
        matched_db_indices = set()
        unmatched_images = []

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
            progress_bar = st.progress(0)
            items = list(images_to_process.items())

            for idx, (img_path, img_bytes) in enumerate(items):
                filename = os.path.basename(img_path)
                folder_dir = os.path.dirname(img_path)
                original_ext = os.path.splitext(filename)[1]
                player_matched = None
                matched_row_idx = None

                cleaned_filename = clean_text(filename)

                # MODE A: GEMINI VISION AI
                if mode == "Gemini Vision AI":
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
                        st.warning(f"Detection bypass on {filename}: {e}")

                # MODE B / FALLBACK: ACCENT-INSENSITIVE FILENAME MATCHING
                if player_matched is None:
                    for db_idx, row in df_db.iterrows():
                        clean_db_player = clean_text(row['Player'])
                        player_parts = clean_db_player.split()
                        last_name = player_parts[-1] if player_parts else clean_db_player

                        if clean_db_player in cleaned_filename or (len(last_name) > 3 and last_name in cleaned_filename):
                            player_matched = row
                            matched_row_idx = db_idx
                            break

                # Save into output zip if matched
                if player_matched is not None:
                    number = str(player_matched['Number'])
                    new_filename = f"{number}{original_ext}"
                    out_path = os.path.join(folder_dir, new_filename) if folder_dir else new_filename

                    zip_out.writestr(out_path, img_bytes)
                    st.write(f"✓ **{img_path}** → Renamed to `{out_path}` ({player_matched['Player']})")
                    processed_count += 1
                    if matched_row_idx is not None:
                        matched_db_indices.add(matched_row_idx)
                else:
                    st.write(f"✕ **{img_path}** → Unmatched in active roster.")
                    unmatched_images.append(img_path)

                progress_bar.progress((idx + 1) / len(items))

        # --- BATCH AUDIT SUMMARY (LEFTOVER DETECTION) ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📊 BATCH AUDIT & LEFTOVER LOGS")
        
        # Calculate leftover database names
        unmatched_db = df_db[~df_db.index.isin(matched_db_indices)]

        audit_col1, audit_col2 = st.columns(2)

        with audit_col1:
            st.markdown(f"##### ⚠️ Extra Unmatched Images ({len(unmatched_images)})")
            if unmatched_images:
                for un_img in unmatched_images:
                    st.caption(f"• `{un_img}`")
            else:
                st.success("Zero leftover images. Every file was matched!")

        with audit_col2:
            st.markdown(f"##### ⚠️ Leftover Roster Players ({len(unmatched_db)})")
            if not unmatched_db.empty:
                for _, row in unmatched_db.iterrows():
                    st.caption(f"• **#{row['Number']}** {row['Player']} ({row['Team']})")
            else:
                st.success("Zero leftover players. Every roster entry received an image!")

        # DOWNLOAD BUTTON
        if processed_count > 0:
            st.download_button(
                label="📦 DOWNLOAD RENAMED ZIP ARCHIVE",
                data=zip_buffer.getvalue(),
                file_name="UCL_Renamed_Assets.zip",
                mime="application/zip"
            )
