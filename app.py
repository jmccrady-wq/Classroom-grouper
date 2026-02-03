import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math
from collections import deque
from PIL import Image
import os
import random

# Set page config for a professional look
st.set_page_config(page_title="Classroom Seating Tool", layout="wide")

def draw_chart_streamlit(tables, period_label, layout_mode, highlight_name=None):
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
        # If this group contains the highlighted student, change the rect style
        group = tables[i]
        has_highlight = False
        if highlight_name is not None:
            for ss in group:
                if str(ss.get('Name', '')) == str(highlight_name):
                    has_highlight = True
                    break

        if has_highlight:
            rect = patches.Rectangle((x-10, y-10), 20, 20, linewidth=2, edgecolor='red', facecolor='#fff0d9')
        else:
            rect = patches.Rectangle((x-10, y-10), 20, 20, linewidth=1, edgecolor='#333', facecolor='#f9f9f9')
        ax.add_patch(rect)
        ax.text(x, y+11, f"Group {i+1}", ha='center', weight='bold', fontsize=9)

        for j, s in enumerate(group):
            name = s.get('Name', '')
            if highlight_name is not None and str(name) == str(highlight_name):
                ax.text(x, y + 6 - (j * 4.5), name, ha='center', fontsize=10, color='red', weight='bold')
            else:
                ax.text(x, y + 6 - (j * 4.5), name, ha='center', fontsize=10)

    plt.axis('off')
    return fig

# --- APP INTERFACE ---
st.title("🍎 Classroom Seating & Grouping Tool")
st.write("Upload your roster to generate balanced, randomized seating charts.")

# SIDEBAR - No personal paths here
st.sidebar.header("Configuration")
uploaded_file = st.sidebar.file_uploader("Upload Roster (Excel)", type="xlsx")

# Visual layout (affects drawing only)
layout_mode = st.sidebar.selectbox("Chart layout", ["Tables", "Grid"])

# Period selector: choose a single period (or All)
period_options = [f"Period {i}" for i in range(1, 10)]
period_options.insert(0, "All Periods")
selected_period = st.sidebar.selectbox("Select period", period_options, index=1)

# Group sizing: either pick exact number of groups, or specify a minimum group size
group_sizing_mode = st.sidebar.radio("Group sizing mode", ["Number of groups", "Minimum group size"])
if group_sizing_mode == "Number of groups":
    num_groups = st.sidebar.number_input("Number of groups", min_value=1, value=7, step=1)
else:
    min_group_size = st.sidebar.number_input("Minimum group size", min_value=1, value=3, step=1)

# Grouping strategy: balance group means or make homogeneous groups
strategy = st.sidebar.radio("Grouping strategy", ["Balanced average skill", "Similar members"]) 

# Reshuffle control stored in session state so button forces new random seed
if 'reshuffle_counter' not in st.session_state:
    st.session_state['reshuffle_counter'] = 0

if uploaded_file:
    all_images = []
    # Layout: full-width for a single selected period, 3-column grid for All Periods
    if selected_period == "All Periods":
        cols = st.columns(3)
        use_multi = True
    else:
        large_container = st.container()
        use_multi = False

    # Decide which periods to show
    if selected_period == "All Periods":
        period_iter = range(1, 10)
    else:
        # Extract number from "Period N"
        try:
            pnum = int(selected_period.split()[1])
            period_iter = [pnum]
        except Exception:
            period_iter = range(1, 10)

    # (Reshuffle button is placed alongside controls within each period's output)

    # Iterate through selected school periods
    for i in period_iter:
        period_name = f"Period {i}"
        try:
            # Read from the uploaded buffer, not a local path
            df = pd.read_excel(uploaded_file, sheet_name=period_name)

            # Ensure session storage for absences and last picks
            if 'absent' not in st.session_state:
                st.session_state['absent'] = {}
            if 'last_pick_groups' not in st.session_state:
                st.session_state['last_pick_groups'] = deque(maxlen=2)

            # Default filter by explicit Status A for initial display
            if 'Status' in df.columns:
                df = df.copy()
                # Keep Status column for initial checkbox defaults but do not drop students yet
            else:
                df = df.copy()

            # Attendance toggles (stored per-period)
            period_absent = set(st.session_state['absent'].get(period_name, []))
            with st.expander(f"Attendance — {period_name}"):
                # Show checkboxes for each student name
                names = []
                if 'Name' in df.columns:
                    names = [str(n) for n in df['Name'].fillna('')]
                for name in names:
                    key = f"absent_{period_name}_{name}"
                    default_checked = (name in period_absent) or (('Status' in df.columns) and (str(df.loc[df['Name'] == name, 'Status'].iloc[0]).strip().upper() == 'A'))
                    checked = st.checkbox(f"Absent: {name}", value=default_checked, key=key)
                    if checked:
                        period_absent.add(name)
                    else:
                        period_absent.discard(name)
            st.session_state['absent'][period_name] = list(period_absent)

            # Filter out absent students before grouping
            if 'Name' in df.columns:
                df_present = df[~df['Name'].astype(str).isin(period_absent)].copy()
            else:
                df_present = df.copy()

            # Stratified Randomization (seeded by reshuffle counter so button forces new groups)
            seed = st.session_state.get('reshuffle_counter', 0)
            groups = [df_present[df_present['Competence'] == comp] for comp in range(10, 0, -1) if 'Competence' in df_present.columns]
            # If Competence not present, just shuffle entire present df
            if not groups:
                try:
                    shuffled_df = df_present.sample(frac=1, random_state=seed)
                except Exception:
                    shuffled_df = df_present.sample(frac=1)
            else:
                shuffled_parts = []
                for idx, g in enumerate(groups):
                    if g.empty:
                        continue
                    try:
                        part = g.sample(frac=1, random_state=(seed + idx * 17))
                    except Exception:
                        part = g.sample(frac=1)
                    shuffled_parts.append(part)
                if shuffled_parts:
                    shuffled_df = pd.concat(shuffled_parts)
                else:
                    shuffled_df = pd.DataFrame(columns=df_present.columns)
            students = shuffled_df.to_dict('records')

            # Determine number of groups `n` according to user choice
            total = len(students)
            if total == 0:
                continue

            if group_sizing_mode == "Number of groups":
                n = min(max(1, int(num_groups)), total)
            else:
                # Use floor division so each group will be at least the minimum size
                # If min_group_size > total this results in 1 group (can't split)
                n = max(1, total // int(min_group_size))

            # Prepare students with numeric competence values (fallback to 0)
            for s in students:
                try:
                    s['_comp'] = float(s.get('Competence', 0))
                except Exception:
                    s['_comp'] = 0.0

            # Build containers according to selected strategy
            containers = [[] for _ in range(n)]

            if strategy == "Balanced average skill":
                # Greedy by group sum while keeping sizes roughly even
                max_size = math.ceil(total / n)
                students_sorted = sorted(students, key=lambda x: x['_comp'], reverse=True)
                group_sums = [0.0] * n
                for s in students_sorted:
                    # Prefer groups that are under max_size
                    candidates = [idx for idx in range(n) if len(containers[idx]) < max_size]
                    if not candidates:
                        candidates = list(range(n))
                    # pick the candidate with smallest sum
                    idx = min(candidates, key=lambda k: group_sums[k])
                    containers[idx].append(s)
                    group_sums[idx] += s['_comp']

            else:  # "Similar members"
                # Group contiguous competence values together
                students_sorted = sorted(students, key=lambda x: x['_comp'], reverse=True)
                base = total // n
                rem = total % n
                start = 0
                for g in range(n):
                    size = base + (1 if g < rem else 0)
                    if size > 0:
                        containers[g] = students_sorted[start:start+size]
                    else:
                        containers[g] = []
                    start += size

            # Randomize order within each group to hide competence levels (seeded)
            for gi, group in enumerate(containers):
                rng = random.Random(seed + gi + i * 13)
                rng.shuffle(group)

            # Render larger single-period view or multi-column grid
            if use_multi:
                with cols[(i-1) % 3]:
                    fig = draw_chart_streamlit(containers, period_name, layout_mode, highlight_name=highlight_name)
                    st.pyplot(fig, use_container_width=True)
            else:
                # For single-period view, place controls before drawing so state updates appear immediately
                with large_container:
                    ctrl_left, ctrl_right = st.columns([3, 1])
                    with ctrl_left:
                        if st.button("Pick random student (different group than last 2)", key=f"pick_{period_name}"):
                            # Build candidate list excluding groups in last picks
                            last_groups = list(st.session_state.get('last_pick_groups', []))
                            candidates = []
                            for gi, group in enumerate(containers):
                                if not group:
                                    continue
                                if gi in last_groups:
                                    continue
                                for s in group:
                                    candidates.append((gi, s))

                            if not candidates:
                                # fallback to any student
                                for gi, group in enumerate(containers):
                                    for s in group:
                                        candidates.append((gi, s))

                            if candidates:
                                gi, picked = random.choice(candidates)
                                st.session_state['last_pick_groups'].append(gi)
                                st.session_state[f'last_picked_{period_name}'] = picked
                            else:
                                st.warning("No students available to pick.")

                    with ctrl_right:
                        if st.button("Reshuffle groups", key=f"reshuffle_{period_name}"):
                            st.session_state['reshuffle_counter'] += 1

                    # After handling controls, determine highlight name for this period (if any)
                    last = st.session_state.get(f'last_picked_{period_name}')
                    highlight_name = None
                    if last and isinstance(last, dict):
                        highlight_name = last.get('Name')

                    fig = draw_chart_streamlit(containers, period_name, layout_mode, highlight_name=highlight_name)
                    st.pyplot(fig, use_container_width=True)

                    # Show last pick below the chart so it matches the highlighted name
                    last = st.session_state.get(f'last_picked_{period_name}')
                    if last and isinstance(last, dict):
                        group_index = st.session_state.get('last_pick_groups')[-1] if st.session_state.get('last_pick_groups') else None
                        if group_index is not None:
                            st.success(f"Last pick: {last.get('Name', 'Unknown')} (Group {group_index+1})")
                        else:
                            st.success(f"Last pick: {last.get('Name', 'Unknown')}")

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
