import streamlit as st
import pandas as pd
import os
import zipfile
import io
import base64
from openai import OpenAI

st.set_page_config(page_title="UCL Image Renamer", layout="centered")
st.title("⚽ UCL Player Image Auto-Renamer")

# --- SIDEBAR: API KEY & OPTIONS ---
st.sidebar.header("Settings")
mode = st.sidebar.radio("Recognition Mode", ["Vision AI (Recognize Face/Jersey)", "Filename Matching (No API Key)"])

api_key = ""
if mode == "Vision AI (Recognize Face/Jersey)":
    api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Get one at platform.openai.com")
    if not api_key:
        st.sidebar.warning("⚠️ Enter an OpenAI API key to use Vision AI recognition.")

# --- STEP 1: UPLOAD DATABASE ---
st.subheader("1. Upload Squad Database")
db_file = st.file_uploader("Upload Excel (.xlsx) or CSV", type=["xlsx", "csv"])

df_db = None
if db_file:
    try:
        df_db = pd.read_excel(db_file) if db_file.name.endswith(".xlsx") else pd.read_csv(db_file)
        df_db.columns = df_db.columns.str.strip()
        st.success(f"Loaded {len(df_db)} players from database!")
        st.dataframe(df_db.head(3), use_container_width=True)
    except Exception as e:
        st.error(f"Error loading database: {e}")

# --- STEP 2: UPLOAD IMAGES ---
st.subheader("2. Upload Player Images")
uploaded_images = st.file_uploader("Drag & drop player images", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)

# --- HELPER FUNCTIONS ---
def identify_with_ai(image_bytes, key):
    client = OpenAI(api_key=key)
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Identify the soccer player in this image. Return ONLY their full name and club team in this format: Player Name, Team Name. Example: Luka Jović, AEK Athens"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }],
        max_tokens=50
    )
    text = response.choices[0].message.content.strip()
    parts = text.split(",")
    return parts[0].strip() if len(parts) > 0 else text

# --- STEP 3: PROCESS & RENAME ---
if st.button("Process & Rename Images"):
    if not df_db is not None:
        st.error("Please upload a database first.")
    elif not uploaded_images:
        st.error("Please upload at least one image.")
    elif mode == "Vision AI (Recognize Face/Jersey)" and not api_key:
        st.error("OpenAI API key is required for Vision AI mode.")
    else:
        zip_buffer = io.BytesIO()
        processed_count = 0

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            progress_bar = st.progress(0)
            
            for idx, img in enumerate(uploaded_images):
                img_bytes = img.read()
                original_ext = os.path.splitext(img.name)[1]
                player_matched = None
                
                # Mode A: Vision AI
                if mode == "Vision AI (Recognize Face/Jersey)":
                    try:
                        detected_name = identify_with_ai(img_bytes, api_key)
                        matches = df_db[df_db['Player'].str.contains(detected_name, case=False, na=False)]
                        if not matches.empty:
                            player_matched = matches.iloc[0]
                    except Exception as e:
                        st.warning(f"Failed AI detection for {img.name}: {e}")

                # Mode B: Filename Matching
                else:
                    for _, row in df_db.iterrows():
                        # Simple match: if player's last name or full name is in filename
                        clean_player = str(row['Player']).lower()
                        if clean_player in img.name.lower():
                            player_matched = row
                            break

                # Save file into ZIP with 100% original quality intact
                if player_matched is not None:
                    number = str(player_matched['Number'])
                    new_filename = f"{number}{original_ext}"
                    zip_file.writestr(new_filename, img_bytes)
                    st.write(f"✅ **{img.name}** → Renamed to `{new_filename}` ({player_matched['Player']})")
                    processed_count += 1
                else:
                    st.write(f"❌ **{img.name}** → No match found in database.")

                progress_bar.progress((idx + 1) / len(uploaded_images))

        # --- DOWNLOAD BUTTON ---
        if processed_count > 0:
            st.success(f"Finished! Successfully renamed {processed_count} images.")
            st.download_button(
                label="📦 Download Renamed Images (.zip)",
                data=zip_buffer.getvalue(),
                file_name="Renamed_Player_Images.zip",
                mime="application/zip"
            )
