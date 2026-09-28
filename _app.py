import io
import os
import re
import unicodedata
import zipfile
from curl_cffi import requests as cffi_requests
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
    scan_mode = st.radio(
        "SCAN MODE",
        [
            "Double Pass (Fast Name Check → AI Fallback)",
            "Filename Matching Only (No AI)",
            "AI Vision Only"
        ]
    )

    api_key = ""
    if "Only (No AI)" not in scan_mode:
        if "GEMINI_API_KEY" in st.secrets:
            api_key = st.secrets["GEMINI_API_KEY"]
            st.success("✓ Milking your API Keys")
        else:
            api_key = st.text_input("Gemini API Key", type="password")
            if not api_key:
                st.warning("⚠️ Enter a Google Gemini API key.")

# --- STRING NORMALIZATION ENGINE ---
def clean_strict(text):
    if not text: return ""
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-zA-Z0-9]', '', text).lower()

def clean_words(text):
    if not text: return []
    text = unicodedata.normalize('NFD', str(text))
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    return [w.lower() for w in text.split() if len(w) > 1]

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

def parse_pasted_text(text, default_team="Bodø/Glimt"):
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    if not lines:
        return None

    rows = []
    for line in lines:
        parts = [p.strip() for p in re.split(r'[\t|]', line) if p.strip()]
        if len(parts) >= 3:
            rows.append({'Player': parts[0], 'Team': parts[1], 'Number': parts[-1]})
        elif len(parts) == 2:
            m_num = re.search(r'\d+', parts[1])
            if m_num:
                rows.append({'Player': parts[0], 'Team': default_team, 'Number': m_num.group(0)})
        else:
            m_end = re.search(r'^(.*?)\s+(\d+)$', line)
            if m_end:
                rows.append({'Player': m_end.group(1).strip(), 'Team': default_team, 'Number': m_end.group(2).strip()})

    df = pd.DataFrame(rows) if rows else None
    if df is not None and not df.empty:
        df = df[~df['Player'].str.lower().isin(['player', 'name', 'full name'])]
    return df

# --- CURL_CFFI UEFA LEAGUE PHASE API SCRAPER ---
# 100% matched to your provided 36 League Phase Teams
UEFA_LEAGUE_PHASE_TEAMS = {
    50124: "AEK Athens",
    50029: "Arsenal",
    50060: "Aston Villa",
    50125: "Atleti",
    50009: "B. Dortmund",
    50080: "Barcelona",
    50030: "Bayern München",
    2601115: "Bodø/Glimt", 
    50008: "Club Brugge",
    2602288: "Como", 
    52692: "Fenerbahçe",
    50012: "Feyenoord",
    50067: "Galatasaray",
    50064: "Inter",
    50148: "LASK",
    50158: "Leipzig",
    52277: "Lens",
    50082: "Lille",
    50050: "Liverpool",
    50065: "Man City",
    52682: "Man Utd",
    50136: "Napoli",
    50043: "Paris",
    50041: "Porto",
    50062: "PSV",
    52265: "Real Betis",
    50051: "Real Madrid",
    50137: "Roma", 
    50122: "S. Bratislava",
    2600527: "Sabah",
    50120: "Shakhtar",
    52061: "Slavia Praha",
    50149: "Sporting CP",
    50139: "Stuttgart",
    50143: "Viking",
    70691: "Villarreal"
}

def fetch_uefa_league_phase_squads_live(status_container, table_container, log_container):
    """Fetches squads securely using curl_cffi to spoof TLS browser signatures."""
    all_players = []
    error_logs = []

    for idx, (team_id, team_name) in enumerate(UEFA_LEAGUE_PHASE_TEAMS.items()):
        status_container.info(f"📡 TLS Impersonation Fetching Team {idx+1}/{len(UEFA_LEAGUE_PHASE_TEAMS)}: **{team_name}**...")
        
        # Calling UEFA directly! No proxies.
        target_url = f"https://comp.uefa.com/v2/teams/{team_id}/squad"
        success = False
        
        try:
            # Impersonate a standard Chrome browser exactly
            res = cffi_requests.get(target_url, impersonate="chrome110", timeout=8)
            
            if res.status_code == 200:
                data = res.json()
                for p in data.get("players", []):
                    num = p.get("shirtNumber") or p.get("jerseyNumber")
                    if num:
                        all_players.append({
                            "Player": p.get("internationalName") or p.get("name"),
                            "Team": team_name,
                            "Number": str(num)
                        })
                success = True
            else:
                error_logs.append(f"❌ {team_name} | HTTP {res.status_code}")
                
        except Exception as e:
            error_logs.append(f"❌ {team_name} | {type(e).__name__} Timeout")
            
        # Continually re-render whatever we have successfully scraped so far
        if all_players:
            temp_df = pd.DataFrame(all_players)
            table_container.dataframe(temp_df, use_container_width=True, height=250)

    status_container.empty()
    
    if error_logs:
        with log_container.expander(f"⚠️ {len(error_logs)} Teams Skipped (Check Logs)", expanded=True):
            st.code("\n".join(error_logs), language="text")
            
    return pd.DataFrame(all_players) if all_players else None

# --- SECTION 1: SQUAD DATA ---
st.markdown("##### [01] ROSTER DATABASE SOURCE")
db_input_method = st.radio(
    "Input Mode", 
    ["Fetch Live League Phase Squads (UEFA.com)", "Paste Roster Text", "Upload File (Excel/CSV/JSON)"], 
    horizontal=True
)

df_db = None

if db_input_method == "Fetch Live League Phase Squads (UEFA.com)":
    
    live_status_ui = st.empty()
    live_table_ui = st.empty()
    live_log_ui = st.empty()
    
    if st.button("⚡ FETCH 36 LEAGUE PHASE SQUADS FROM UEFA.COM"):
        df_fetched = fetch_uefa_league_phase_squads_live(live_status_ui, live_table_ui, live_log_ui)
        
        if df_fetched is not None and not df_fetched.empty:
            st.session_state['df_db'] = df_fetched
            missing_teams_count = len(UEFA_LEAGUE_PHASE_TEAMS) - df_fetched['Team'].nunique()
            
            if missing_teams_count > 0:
                st.success(f"✓ Partial Success: Loaded {len(df_fetched)} players across {df_fetched['Team'].nunique()} Clubs. Skipped {missing_teams_count} clubs automatically.")
            else:
                st.success(f"✓ Total Victory: Loaded {len(df_fetched)} League Phase Players across all 36 Clubs!")
        else:
            st.error("Could not fetch UEFA League Phase data. All requests failed/timed out.")

    if 'df_db' in st.session_state:
        df_db = st.session_state['df_db']

elif db_input_method == "Upload File (Excel/CSV/JSON)":
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
    default_team_input = st.text_input("Fallback Club Name", value="Bodø/Glimt")
    pasted_text = st.text_area(
        "Paste Roster Content",
        height=180,
        placeholder="Julian Faye Lund\tBodø/Glimt | Bodø/Glimt | 1\nVillads Nielsen\tBodø/Glimt | Bodø/Glimt | 2"
    )
    if pasted_text:
        df_db = parse_pasted_text(pasted_text, default_team=default_team_input)
        if df_db is not None and not df_db.empty:
            st.success(f"✓ Parsed {len(df_db)} Athletes successfully!")

# --- DISPLAY LIVE SQUAD TABLE ON SCREEN ---
if df_db is not None and not df_db.empty and db_input_method != "Fetch Live League Phase Squads (UEFA.com)":
    st.markdown("---")
    st.markdown("### 📊 LIVE ROSTER DATABASE")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Athletes Loaded", len(df_db))
    with col2:
        st.metric("Total Clubs Represented", df_db['Team'].nunique())
        
    selected_club = st.selectbox("Filter Roster Screen by Club", ["ALL CLUBS"] + list(df_db['Team'].unique()))
    
    if selected_club != "ALL CLUBS":
        display_df = df_db[df_db['Team'] == selected_club]
    else:
        display_df = df_db

    st.dataframe(display_df, use_container_width=True, height=350)
elif df_db is not None and not df_db.empty:
    st.markdown("---")
    st.markdown("### 📊 LIVE ROSTER DATABASE")
    selected_club = st.selectbox("Filter Roster Screen by Club", ["ALL CLUBS"] + list(df_db['Team'].unique()))
    
    if selected_club != "ALL CLUBS":
        display_df = df_db[df_db['Team'] == selected_club]
        st.dataframe(display_df, use_container_width=True, height=350)

st.markdown("<br>", unsafe_allow_html=True)

# --- SECTION 2: ASSETS & FOLDERS ---
st.markdown("##### [02] MEDIA ASSETS & FOLDERS")
asset_input_method = st.radio("Asset Source", ["Drag & Drop Files / .ZIP Archive", "Local Folder Directory Path"], horizontal=True)

images_to_process = {}

if asset_input_method == "Drag & Drop Files / .ZIP Archive":
    uploaded_files = st.file_uploader(
        "Drop Individual Images OR a .ZIP Archive",
        type=["zip", "png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True
    )

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

else:
    folder_path = st.text_input("Paste Local Folder Path", placeholder="e.g. C:/Users/Hawk-Eye/Pictures/RAW Images")
    if folder_path and os.path.exists(folder_path):
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, folder_path)
                    try:
                        with open(full_p, "rb") as img_f:
                            images_to_process[rel_p] = img_f.read()
                    except Exception as e:
                        st.warning(f"Could not read file {full_p}: {e}")
        if images_to_process:
            st.success(f"Found {len(images_to_process)} image files inside `{folder_path}`")
    elif folder_path:
        st.error(f"Directory path `{folder_path}` does not exist or is inaccessible.")

if images_to_process:
    st.write(f"Total Processing Queue: **{len(images_to_process)}** media files ready.")

# --- VISION AI RECOGNITION ---
def identify_with_gemini(image_bytes, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-3.6-flash')
    img = Image.open(io.BytesIO(image_bytes))
    prompt = (
        "Identify the soccer player and their club team in this image. "
        "Return ONLY their full name and club team in this exact format: "
        "Player Name, Team Name."
    )
    response = model.generate_content([prompt, img])
    parts = response.text.strip().split(",")
    return parts[0].strip() if len(parts) > 0 else response.text.strip()

# --- SECTION 3: SCAN EXECUTION ---
st.markdown("<br>", unsafe_allow_html=True)
if st.button("EXECUTE SCAN ENGINE"):
    if df_db is None or df_db.empty:
        st.error("No valid roster loaded.")
    elif not images_to_process:
        st.error("No image assets provided.")
    elif "Only (No AI)" not in scan_mode and not api_key:
        st.error("Gemini API Key required for AI modes.")
    else:
        zip_buffer = io.BytesIO()
        matched_db_indices = set()
        unmatched_images = []
        
        final_matched = {}
        ai_queue = {}

        items = list(images_to_process.items())
        total_items = len(items)

        # MODE 1 & 2: LOCAL FILENAME MATCHING PASS
        if "AI Vision Only" not in scan_mode:
            st.markdown("#### ⚡ PASS 1: FAST LOCAL FILENAME MATCHING")
            p1_bar = st.progress(0)

            for idx, (img_path, img_bytes) in enumerate(items):
                filename = os.path.basename(img_path)
                strict_filename = clean_strict(filename)
                file_words = set(clean_words(filename))
                
                player_matched = None
                matched_row_idx = None

                for db_idx, row in df_db.iterrows():
                    player_name_raw = str(row['Player'])
                    strict_player = clean_strict(player_name_raw)
                    player_words = set(clean_words(player_name_raw))

                    if strict_player and strict_player in strict_filename:
                        player_matched = row
                        matched_row_idx = db_idx
                        break

                    if player_words and player_words.issubset(file_words):
                        player_matched = row
                        matched_row_idx = db_idx
                        break

                if player_matched is not None:
                    final_matched[img_path] = (player_matched, img_bytes)
                    matched_db_indices.add(matched_row_idx)
                    st.write(f"⚡ **[Name Match]** `{img_path}` → Renamed to `{player_matched['Number']}` ({player_matched['Player']})")
                else:
                    ai_queue[img_path] = img_bytes

                p1_bar.progress((idx + 1) / total_items)

            st.success(f"Filename Matching Complete! Resolved {len(final_matched)} / {total_items} images locally.")
        else:
            ai_queue = dict(items)

        # MODE 1 & 3: GEMINI AI VISION PASS
        if ai_queue and "Only (No AI)" not in scan_mode:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"#### 🧠 GEMINI AI VISION SCAN ({len(ai_queue)} Images)")
            p2_bar = st.progress(0)
            ai_items = list(ai_queue.items())

            for idx, (img_path, img_bytes) in enumerate(ai_items):
                filename = os.path.basename(img_path)
                player_matched = None
                matched_row_idx = None

                try:
                    detected_name = identify_with_gemini(img_bytes, api_key)
                    strict_detected = clean_strict(detected_name)

                    for db_idx, row in df_db.iterrows():
                        strict_player = clean_strict(row['Player'])
                        if strict_player in strict_detected or strict_detected in strict_player:
                            player_matched = row
                            matched_row_idx = db_idx
                            break
                            
                except Exception as e:
                    error_msg = f"HTTP/API Error: {type(e).__name__} - {str(e)}"
                    st.warning(f"⚠️ AI bypass on `{filename}`: {error_msg}")
                    unmatched_images.append(img_path)
                    continue

                if player_matched is not None:
                    final_matched[img_path] = (player_matched, img_bytes)
                    matched_db_indices.add(matched_row_idx)
                    st.write(f"🧠 **[AI Match]** `{img_path}` → Renamed to `{player_matched['Number']}` ({player_matched['Player']})")
                else:
                    st.write(f"✕ `{img_path}` → Unmatched.")
                    unmatched_images.append(img_path)

                p2_bar.progress((idx + 1) / len(ai_items))

        elif ai_queue and "Only (No AI)" in scan_mode:
            for img_path in ai_queue.keys():
                unmatched_images.append(img_path)

        # WRITE OUTPUT ZIP & RENDER CONSOLES
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
            for img_path, (player_row, img_bytes) in final_matched.items():
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

        if len(final_matched) > 0:
            st.download_button(
                label="📦 DOWNLOAD RENAMED ZIP ARCHIVE",
                data=zip_buffer.getvalue(),
                file_name="UCL_Renamed_Assets.zip",
                mime="application/zip"
            )
