import streamlit as st
import pandas as pd
import os

st.title("UCL Player Image Renamer")

# 1. Database Drag & Drop
db_file = st.file_uploader("Upload Database (.xlsx or .csv)", type=["xlsx", "csv"])
df_db = None

if db_file:
    df_db = pd.read_excel(db_file) if db_file.name.endswith(".xlsx") else pd.read_csv(db_file)
    st.success(f"Database Loaded: {len(df_db)} players found")

# 2. Image Batch Upload
image_files = st.file_uploader("Upload Player Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if st.button("Process Images") and df_db is not None and image_files:
    for img in image_files:
        # Vision AI identification step goes here
        player_name, team_name = "Luka Jović", "AEK Athens" 
        
        match = df_db[(df_db['Player'].str.contains(player_name, case=False, na=False))]
        if not match.empty:
            squad_num = match.iloc[0]['Number']
            st.write(f"Matched **{img.name}** to **{player_name}** -> `{squad_num}.png`")
            # Offer downloadable renamed file
