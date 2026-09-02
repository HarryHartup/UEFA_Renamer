import streamlit as st
import pandas as pd
import os
import zipfile
import io
import re
from PIL import Image
import google.generativeai as genai

# Must be the first Streamlit command
st.set_page_config(page_title="Squad Image Studio", layout="wide", page_icon="⭐")

# --- STYLE ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {background-color: transparent !important;}

.stApp {
    background: radial-gradient(circle at 50% 0%, #10204f 0%, #050a1c 55%, #03050f 100%) !important;
}

.block-container {
    background: rgba(7, 14, 38, 0.72) !important;
    backdrop-filter: blur(10px) !important;
    -webkit-backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(180, 195, 230, 0.14);
    border-radius: 6px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    padding: 3rem !important;
    margin-top: 2.5rem !important;
    margin-bottom: 3rem !important;
    max-width: 880px !important;
    animation: fadeUp 0.6s ease;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

h1, h2, h3, p, label, .stRadio > div, .stMarkdown, .stText, span {
    font-family: 'Inter', sans-serif !important;
    color: #e7ecfb !important;
}

/* Title: restrained, structural, no rainbow shimmer */
h1 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 2.6rem !important;
    color: #ffffff !important;
    text-align: left;
    border-bottom: 1px solid rgba(180, 195, 230, 0.18);
    padding-bottom: 1rem;
    margin-bottom: 0 !important;
    position: relative;
}
h1::after {
    content: "";
    position: absolute;
    left: 0; bottom: -1px;
    width: 64px; height: 2px;
    background: linear-gradient(90deg, #c9d4ee, transparent);
}
.subtitle {
    font-family: 'Inter', sans-serif;
    color: #8b96bd !important;
    font-size: 0.95rem;
    margin-top: 0.6rem;
    margin-bottom: 2.2rem;
    letter-spacing: 0.01em;
}

h3 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 1.15rem !important;
    color: #cdd7f2 !important;
    margin-top: 2.2rem !important;
    margin-bottom: 0.9rem !important;
}

/* Buttons: solid navy, subtle silver edge, no neon glow */
.stButton > button {
    background: linear-gradient(180deg, #1c2c63 0%, #101a3f 100%) !important;
    color: #f2f4fc !important;
    border: 1px solid rgba(180, 195, 230, 0.35) !important;
    border-radius: 4px !important;
    padding: 0.7rem 2rem !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-size: 0.95rem;
    box-shadow: 0 6px 18px rgba(0,0,0,0.35) !important;
    transition: all 0.25s ease !important;
    width: 100%;
}
.stButton > button:hover {
    border-color: rgba(230, 236, 255, 0.7) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 10px 26px rgba(0,0,0,0.45) !important;
}

.stDownloadButton > button {
    background: linear-gradient(180deg, #2a3f8f 0%, #16215a 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(200, 210, 240, 0.4) !important;
    border-radius: 4px !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0.7rem 2rem !important;
    width: 100%;
}
.stDownloadButton > button:hover {
    box-shadow: 0 10px 26px rgba(30,60,150,0.4) !important;
}

/* File uploader */
[data-testid="stFileUploadDropzone"] {
    background-color: rgba(255, 255, 255, 0.025) !important;
    border: 1px dashed rgba(180, 195, 230, 0.3) !important;
    border-radius: 6px !important;
    transition: all 0.25s ease !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    background-color: rgba(180, 195, 230, 0.06) !important;
    border-color: rgba(200, 210, 240, 0.55) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: rgba(4, 8, 22, 0.92) !important;
    border-right: 1px solid rgba(180, 195, 230, 0.12);
}
[data-testid="stSidebar"] h3 {
    color: #9fadd6 !important;
    font-size: 0.95rem !important;
}

/* Inputs */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background-color: rgba(255,255,255,0.04) !important;
    color: #f0f2fb !important;
    border: 1px solid rgba(180, 195, 230, 0.25) !important;
    border-radius: 4px !important;
}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border: 1px solid rgba(200, 210, 240, 0.6) !important;
    box-shadow: 0 0 0 2px rgba(180, 195, 230, 0.12) !important;
}

/* Progress bar: quiet steel-blue, not neon */
div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #2a3f8f, #6478c9) !important;
}

/* Result lines during processing */
.match-line { font-family: 'Inter', sans-serif; font-size: 0.92rem; padding: 2px 0; }
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

st.sidebar.markdown("---")
st.sidebar.markdown("### Background")
bg_video_file = st.sidebar.file_uploader(
    "Optional stadium video (.mp4)",
    type=["mp4"],
    help="Loops quietly behind the page, dimmed for readability."
)
if bg_video_file is not None:
    import base64
    video_b64 = base64.b64encode(bg_video_file.read()).decode()
    st.markdown(f"""
        <video autoplay loop muted playsinline
            style="position: fixed; right: 0; bottom: 0; min-width: 100%; min-height: 100%;
                   z-index: -100; object-fit: cover; filter: brightness(0.28) saturate(1.05);">
          <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
        </video>
        <div style="position: fixed; inset: 0; z-index: -99; pointer-events: none;
                    background: radial-gradient(circle at 50% 0%, rgba(16,32,79,0.35) 0%, rgba(3,5,15,0.75) 70%);">
        </div>
    """, unsafe_allow_html=True)


# --- HEADER ---
st.title("⭐ Squad Image Studio")
st.markdown('<div class="subtitle">Match player photos to shirt numbers and rename an entire squad in one pass.</div>', unsafe_allow_html=True)


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
st.markdown("### 1. Squad List")
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


# --- STEP 2: IMAGES ---
st.markdown("### 2. Player Photos")
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
st.markdown("### 3. Rename & Download")

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
                    st.markdown(f'<div class="match-line">✓ {img_path} → <b>{out_path}</b> ({player_matched["Player"]})</div>', unsafe_allow_html=True)
                    processed_count += 1
                else:
                    st.markdown(f'<div class="match-line" style="color:#c98a8a !important;">— {img_path} → no match found</div>', unsafe_allow_html=True)

                progress_bar.progress((idx + 1) / len(items))

        if processed_count > 0:
            st.success(f"Renamed {processed_count} of {len(items)} images.")
            st.download_button(
                "Download renamed photos (.zip)",
                data=zip_buffer.getvalue(),
                file_name="Renamed_Player_Images.zip",
                mime="application/zip"
            )
