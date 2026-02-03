import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import os
import random

# Set page config for a professional look
st.set_page_config(page_title="Classroom Seating Tool", layout="wide")

def draw_chart_streamlit(tables, period_label, layout_mode):
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_title(f"{period_label}: {layout_mode}", fontsize=16, pad=15)
    
    # Layout Logic
    if "Table" in layout_mode:
        coords = [(12, 65), (37, 65), (62, 65), (87, 65), (25, 25), (50, 25), (75, 25)]
    else: 
        coords = [(x, y) for y in [75, 50, 25] for x in [15, 40, 65, 90]]

    for i, (x, y) in enumerate(coords):
        if i >= len(tables): break
        rect = patches.Rectangle((x-10, y-10), 20, 20, linewidth=1, edgecolor='#333', facecolor='#f9f9f9')
        ax.add_patch(rect)
        ax.text(x, y+11, f"Group {i+1}", ha='center', weight='bold', fontsize=9)
        
        for j, s in enumerate(tables[i]):
            ax.text(x, y + 6 - (j * 4.5), s['Name'], ha='center', fontsize=10)

    plt.axis('off')
    return fig

# --- APP INTERFACE ---
st.title("🍎 Classroom Seating & Grouping Tool")
st.write("Upload your roster to generate balanced, randomized seating charts.")

# SIDEBAR - No personal paths here
st.sidebar.header("Configuration")
uploaded_file = st.sidebar.file_uploader("Upload Roster (Excel)", type="xlsx")
mode = st.sidebar.radio("Grouping Style", ["Pairs (Similar Ability)", "Groups of 3-4 (Balanced)", "7 Tables (Spread)"])

if uploaded_file:
    all_images = []
    cols = st.columns(3)
    
    # Iterate through standard school periods
    for i in range(1, 10):
        period_name = f"Period {i}"
        try:
            # Read from the uploaded buffer, not a local path
            df = pd.read_excel(uploaded_file, sheet_name=period_name)
            
            # Filter Absences
            if 'Status' in df.columns:
                df = df[df['Status'].astype(str).str.upper() != 'A']
            
            # Stratified Randomization
            groups = [df[df['Competence'] == comp] for comp in range(10, 0, -1)]
            shuffled_df = pd.concat([g.sample(frac=1) for g in groups if not g.empty])
            students = shuffled_df.to_dict('records')

            # Grouping Math
            if "Pairs" in mode:
                n = (len(students) + 1) // 2
                limit = 2
            elif "Groups" in mode:
                n = max(1, len(students) // 3)
                limit = 4
            else:
                n = 7
                limit = 4

            containers = [[] for _ in range(n)]
            for j, s in enumerate(students):
                idx = j % n
                if len(containers[idx]) < limit:
                    containers[idx].append(s)

            # Randomize order within the group to hide competence levels
            for group in containers:
                random.shuffle(group)

            with cols[(i-1) % 3]:
                fig = draw_chart_streamlit(containers, period_name, mode)
                st.pyplot(fig)
                
                # Use os.path.join for system-agnostic paths
                temp_filename = f"temp_p{i}.png"
                fig.savefig(temp_filename, dpi=100)
                all_images.append(temp_filename)

        except Exception:
            # Silently skip periods that don't exist in the Excel
            continue

    if all_images:
        pdf_output = "Seating_Charts.pdf"
        imgs = [Image.open(f).convert('RGB') for f in all_images]
        imgs[0].save(pdf_output, save_all=True, append_images=imgs[1:])
        
        with open(pdf_output, "rb") as f:
            st.sidebar.download_button("📥 Download PDF", f, file_name=pdf_output)
        
        # Cleanup temp files
        for f in all_images: 
            if os.path.exists(f): os.remove(f)
else:
    st.info("👋 Welcome! Please upload an Excel file with tabs named 'Period 1' through 'Period 9' to begin.")