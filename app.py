import streamlit as st
import pandas as pd
import os
import zipfile
import io
import re
from PIL import Image
import google.generativeai as genai

st.set_page_config(page_title="UCL Image Renamer", layout="centered")
st.title("⚽ UCL Player Image Auto-Renamer")

# --- SIDEBAR: API KEY & SETTINGS ---
st.sidebar.header("Settings")
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
            # Filter out header row if present
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
            # Match "1 Player Name" or "Player Name 1"
            m_start = re.match(r'^(\d+)\s+(.+)$', line)
            m_end = re.search(r'^(.*?)\s+(\d+)$', line)
            if m_start:
                rows.append({'Player': m_start.group(2).strip(), 'Team': default_team, 'Number': m_start.group(1).strip()})
            elif m_end:
                rows.append({'Player': m_end.group(1).strip(), 'Team': default_team, 'Number': m_end.group(2).strip()})

    return pd.DataFrame(rows) if rows else None


# --- STEP 1: SQUAD DATABASE / LIST ---
st.subheader("1. Squad Database / Player List")
db_input_method = st.radio("Input Method", ["Upload Excel/CSV File", "Paste Player List Text"], horizontal=True)

df_db = None

if db_input_method == "Upload Excel/CSV File":
    db_file = st.file_uploader("Upload Excel (.xlsx) or CSV", type=["xlsx", "csv"])
    if db_file:
        try:
            df_raw = pd.read_excel(db_file) if db_file.name.endswith(".xlsx") else pd.read_csv(db_file)
            df_db = normalize_df(df_raw)
            st.success(f"Loaded {len(df_db)} players from file!")
        except Exception as e:
            st.error(f"Error reading file: {e}")

else: # Paste Text
    default_team_input = st.text_input("Default Team Name (if not specified in text)", value="AEK Athens")
    pasted_text = st.text_area(
        "Paste Player List Here",
        height=180,
        placeholder="Example:\nThomas Strakosha | AEK Athens | 1\nHarold Moukoudi | AEK Athens | 2\n\nOR:\n1 Thomas Strakosha\n2 Harold Moukoudi"
    )
    if pasted_text:
        df_db = parse_pasted_text(pasted_text, default_team=default_team_input)
        if df_db is not None and not df_db.empty:
            st.success(f"Parsed {len(df_db)} players from pasted text!")
        else:
            st.error("Could not parse player list. Please check format.")

if df_db is not None and not df_db.empty:
    st.dataframe(df_db.head(5), use_container_width=True)


# --- STEP 2: UPLOAD IMAGES / SUBFOLDERS ---
st.subheader("2. Upload Player Images or Folders")
st.info("💡 **Subfolder Tip:** To preserve and search nested subfolders, upload a **`.zip` archive** containing your folders!")

uploaded_files = st.file_uploader(
    "Drag & drop image files OR a .zip archive containing subfolders",
    type=["png", "jpg", "jpeg", "webp", "zip"],
    accept_multiple_files=True
)

images_to_process = {} # {relative_path: bytes}

if uploaded_files:
    for f in uploaded_files:
        if f.name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(f, 'r') as z:
                    for file_info in z.infolist():
                        # Skip directories and system metadata (like __MACOSX)
                        if not file_info.is_dir() and not file_info.filename.startswith('__MACOSX'):
                            if file_info.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                                images_to_process[file_info.filename] = z.read(file_info)
                st.success(f"Extracted {len(images_to_process)} images from subfolders inside `{f.name}`")
            except Exception as e:
                st.error(f"Error unzipping {f.name}: {e}")
        elif f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            images_to_process[f.name] = f.read()

    if images_to_process:
        st.write(f"Total Images Ready for Processing: **{len(images_to_process)}**")


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


# --- STEP 3: PROCESS & RENAME ---
if st.button("Process & Rename Images"):
    if df_db is None or df_db.empty:
        st.error("Please load or paste a database first.")
    elif not images_to_process:
        st.error("Please upload at least one image or zip file.")
    elif mode == "Gemini Vision AI (Recognize Face/Jersey)" and not api_key:
        st.error("Gemini API key is required for Vision AI mode.")
    else:
        zip_buffer = io.BytesIO()
        processed_count = 0

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_out:
            progress_bar = st.progress(0)
            items = list(images_to_process.items())

            for idx, (img_path, img_bytes) in enumerate(items):
                filename = os.path.basename(img_path)
                folder_dir = os.path.dirname(img_path) # Preserves subfolder structure
                original_ext = os.path.splitext(filename)[1]
                player_matched = None

                # Mode A: Gemini Vision AI
                if mode == "Gemini Vision AI (Recognize Face/Jersey)":
                    try:
                        detected_name = identify_with_gemini(img_bytes, api_key)
                        matches = df_db[df_db['Player'].str.contains(detected_name, case=False, na=False)]
                        if not matches.empty:
                            player_matched = matches.iloc[0]
                    except Exception as e:
                        st.warning(f"Failed AI detection for {filename}: {e}")

                # Mode B: Filename Matching
                else:
                    for _, row in df_db.iterrows():
                        clean_player = str(row['Player']).lower()
                        if clean_player in filename.lower():
                            player_matched = row
                            break

                # Save file into output ZIP with subfolder structure preserved
                if player_matched is not None:
                    number = str(player_matched['Number'])
                    new_filename = f"{number}{original_ext}"
                    out_path = os.path.join(folder_dir, new_filename) if folder_dir else new_filename

                    zip_out.writestr(out_path, img_bytes)
                    st.write(f"✅ **{img_path}** → Renamed to `{out_path}` ({player_matched['Player']})")
                    processed_count += 1
                else:
                    st.write(f"❌ **{img_path}** → No match found in database.")

                progress_bar.progress((idx + 1) / len(items))

        # Download ZIP
        if processed_count > 0:
            st.success(f"Finished! Successfully renamed {processed_count} images.")
            st.download_button(
                label="📦 Download Renamed Images (.zip)",
                data=zip_buffer.getvalue(),
                file_name="Renamed_Player_Images.zip",
                mime="application/zip"
            )
