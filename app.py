# LANDING PAGE IMAGE LINK:  "https://raw.githubusercontent.com/Lagunis/fantasy-playoff-app/refs/heads/main/football_intro.png"

import streamlit as st
import pandas as pd
import gspread
import hashlib
import os
from datetime import datetime, timezone

st.set_page_config(layout="wide", page_title="Champions League")

# --- ⚙️ COMMISSIONER CONTROLS ⚙️ ---
CURRENT_WEEK = 4

# --- ⚠️ PASTE YOUR GITHUB IMAGE LINK HERE ⚠️ ---
BACKGROUND_IMAGE_URL = "https://raw.githubusercontent.com/Lagunis/fantasy-playoff-app/refs/heads/main/football_intro.png"


# --- 1. SECURITY & DATABASE SETUP ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

def get_connection():
    if "gcp_service_account" not in st.secrets:
        st.error("Secrets not found! Check your Streamlit Settings.")
        return None
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    return gc

# --- 2. CSS & STYLING ---
def set_bg_from_url(url):
    st.markdown(
         f"""
         <style>
         @import url('https://fonts.googleapis.com/css2?family=Nanum+Brush+Script&display=swap');
         @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&display=swap');
         @import url('https://fonts.googleapis.com/css2?family=Roboto+Slab:wght@400;700&display=swap');

         .stApp {{
             background-image: url("{url}");
             background-size: cover;
             background-position: center;
             background-repeat: no-repeat;
             background-attachment: fixed;
         }}
         
         header {{visibility: hidden;}}
         
         .spartan-blood {{
             font-family: 'Nanum Brush Script', cursive;
             font-size: 130px !important;
             color: #8B0000;
             text-shadow: 4px 4px 0px #000000;
             line-height: 0.9;
             margin-bottom: 10px;
             transform: rotate(-3deg);
         }}
         
         .spartan-sub {{
             font-family: 'Cinzel', serif;
             font-size: 35px !important;
             color: #e0e0e0;
             text-shadow: 2px 2px 4px #000000;
             letter-spacing: 5px;
             font-weight: 700;
             margin-top: 5px;
         }}

         div[data-testid="stTabs"] {{
             background-color: rgba(0, 0, 0, 0.80) !important; 
             border: 2px solid #8B0000;
             border-radius: 15px;
             padding: 25px;
             box-shadow: 0 0 40px rgba(139, 0, 0, 0.6); 
             color: white !important;
         }}
         
         button[data-baseweb="tab"] {{ color: white !important; }}
         div[data-baseweb="tab-highlight"] {{ background-color: #8B0000 !important; }}
         
         label {{ color: white !important; }}
         input {{ color: black !important; }}

         div[data-testid="stExpander"] {{
             background-color: rgba(15, 15, 15, 0.95) !important;
             border: 1px solid #8B0000 !important;
         }}
         div[data-testid="stExpander"] p, 
         div[data-testid="stExpander"] li {{
             color: #E0E0E0 !important;
             font-family: 'Roboto Slab', serif !important;
             font-size: 16px !important;
         }}
         div[data-testid="stExpander"] h3 {{
             color: #FBBF24 !important;
             font-family: 'Cinzel', serif !important;
             margin-top: 15px !important;
         }}
         
         div[data-testid="stExpander"] table {{
             color: white !important;
             border-collapse: collapse !important;
         }}
         div[data-testid="stExpander"] th {{
             color: #FBBF24 !important;
             border-bottom: 1px solid #555 !important;
             text-align: left !important;
         }}
         div[data-testid="stExpander"] td {{
             color: #E0E0E0 !important;
             border-bottom: 1px solid #333 !important;
         }}
         
         div[data-testid="stTabs"] button[kind="primary"] {{
             background-color: #991B1B !important; 
             color: white !important;
             border: 1px solid #F87171 !important;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

def apply_war_room_style():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: none !important;
            background-color: #0F172A !important; 
        }
        h1, h2, h3, h4, h5, h6, p, li, label {
            color: #E2E8F0 !important; 
        }
        h1, h2, h3 {
            font-family: 'Cinzel', serif !important;
            color: #60A5FA !important; 
            text-shadow: 1px 1px 2px black;
        }
        
        button[kind="primary"] {
            background-color: #7C3AED !important;
            color: white !important;
            border: 1px solid #A78BFA !important;
        }
        
        button[kind="secondary"] {
            background-color: #334155 !important;
            color: #E2E8F0 !important;
            border: 1px solid #475569 !important;
        }
        
        button[title="save_roster_btn"] {
            background-color: #15803d !important;
            color: white !important;
            border: 1px solid #4ade80 !important;
            font-size: 18px !important;
        }
        button[title="save_roster_btn"]:hover {
            background-color: #166534 !important;
        }
        
        button:disabled {
            background-color: #7F1D1D !important;
            color: #FECACA !important;
            border: 1px solid #B91C1C !important;
            opacity: 1.0 !important;
            cursor: not-allowed;
        }

        [data-testid="stDataEditor"] {
            border: 1px solid #334155;
            border-radius: 5px;
            background-color: #1E293B; 
        }
        [data-testid="stMetricValue"] {
            color: #FBBF24 !important; 
        }
        section[data-testid="stSidebar"] {
            background-color: #0B1120 !important;
            border-right: 1px solid #334155;
        }
        label[data-baseweb="checkbox"] {
            color: #E2E8F0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. AUTH FUNCTIONS ---
def create_user(email, password, manager_name):
    try:
        gc = get_connection()
        sh = gc.open("fantasy_league_db")
        worksheet = sh.worksheet("users")
        df = pd.DataFrame(worksheet.get_all_records())
        if not df.empty and email in df['email'].values:
            return False, "Email already registered."
        new_user = [email, make_hashes(password), manager_name]
        worksheet.append_row(new_user)
        return True, "Account created!"
    except Exception as e:
        return False, f"Database Error: {e}"

def verify_login(email, password):
    try:
        gc = get_connection()
        sh = gc.open("fantasy_league_db")
        worksheet = sh.worksheet("users")
        df = pd.DataFrame(worksheet.get_all_records())
        if df.empty: return False, "No users found."
        if email in df['email'].values:
            user_row = df[df['email'] == email].iloc[0]
            if check_hashes(password, user_row['password']):
                return True, user_row['manager_name'], user_row['email']
    except Exception as e:
        return False, f"Login Error: {e}", ""
    return False, "Incorrect email or password.", ""

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'manager_name' not in st.session_state: st.session_state['manager_name'] = ""
if 'user_email' not in st.session_state: st.session_state['user_email'] = "" 
if 'my_roster' not in st.session_state: st.session_state['my_roster'] = []
if 'roster_loaded' not in st.session_state: st.session_state['roster_loaded'] = False
if 'current_page' not in st.session_state: st.session_state['current_page'] = "War Room" 

# --- 5. PAGE NAVIGATION COMPONENT ---
def render_navbar():
    c1, c2, c3, c4 = st.columns([1, 1, 4, 1])
    
    with c1:
        if st.button("⚔️ WAR ROOM", use_container_width=True, type="primary" if st.session_state['current_page'] == "War Room" else "secondary"):
            st.session_state['current_page'] = "War Room"
            st.rerun()
            
    with c2:
        if st.button("🏛️ COLOSSEUM", use_container_width=True, type="primary" if st.session_state['current_page'] == "Leaderboard" else "secondary"):
            st.session_state['current_page'] = "Leaderboard"
            st.rerun()
            
    with c4:
        if st.button("LOG OUT", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.session_state['roster_loaded'] = False
            st.session_state['my_roster'] = []
            st.session_state['user_email'] = ""
            st.session_state['current_page'] = "War Room"
            st.rerun()
    
    st.divider()

# --- 6. LANDING PAGE ---
def login_page():
    set_bg_from_url(BACKGROUND_IMAGE_URL)

    col_title, col_space, col_login = st.columns([4, 1, 2])
    
    with col_title:
        st.markdown('<br>', unsafe_allow_html=True)
        st.markdown(
            '''
            <div style="text-align: left;">
                <p class="spartan-blood">CHAMPIONS<br>LEAGUE</p>
                <p class="spartan-sub">2026 NFL PLAYOFFS</p>
            </div>
            ''', 
            unsafe_allow_html=True
        )

    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔐 ENTER", "📝 JOIN"])
        
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type='password', key="login_pass")
            if st.button("LOG IN", use_container_width=True, type="primary"):
                is_valid, name, user_mail = verify_login(email, password)
                if is_valid:
                    st.session_state['logged_in'] = True
                    st.session_state['manager_name'] = name
                    st.session_state['user_email'] = user_mail
                    st.session_state['roster_loaded'] = False 
                    st.rerun()
                else:
                    st.error(name)
                    
        with tab2:
            new_email = st.text_input("Email", key="signup_email")
            new_user_name = st.text_input("Manager Name", key="signup_name")
            new_password = st.text_input("Password", type='password', key="signup_pass")
            if st.button("SIGN UP", use_container_width=True, type="primary"):
                if new_email and new_password and new_user_name:
                    success, msg = create_user(new_email, new_password, new_user_name)
                    if success: 
                        st.success(msg)
                        st.session_state['logged_in'] = True
                        st.session_state['manager_name'] = new_user_name
                        st.session_state['user_email'] = new_email
                        st.session_state['roster_loaded'] = False
                        st.rerun()
                    else: st.error(msg)
                else:
                    st.warning("Missing info")

    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    c_left, c_center, c_right = st.columns([1, 2, 1])
    with c_center:
        with st.expander("📜 RULES OF THE ARENA (Read Carefully)", expanded=False):
            st.markdown("""
            ### ⚔️ The Format
            * **Duration:** The contest spans all **4 Weeks** of the NFL Playoffs.
            * **Objective:** The Manager with the **Highest Cumulative Total Points** wins.
            * **Player Pool:** Players are **NOT unique**.
            
            ### 💰 Stakes & Payouts
            * **Entry Fee:** **$40**.
            * **Payout:** **9 total entries for 360.  1st = 180, 2nd = 120, 3rd = 60**
            
            ### 🚀 The Multiplier Strategy
            Start the same player consecutively to boost their score.
            * **Week 1:** 100% (1.0x)
            * **Week 2 Streak:** 125% (1.25x)
            * **Week 3 Streak:** 150% (1.5x)
            * **Week 4 Streak:** 200% (2.0x)

            ### 📋 Roster (10 Players)
            1 QB, 2 RB, 2 WR, 1 TE, 2 FLEX, 1 K, 1 DEF.

            ### For Scoring and Standings, please see Google Sheets
            """)

# --- 7. LEADERBOARD PAGE ---
def leaderboard_page():
    apply_war_room_style()
    render_navbar()
    
    st.title("🏛️ The Colosseum")
    st.caption("Current Standings & Manager Directory")
    
    try:
        gc = get_connection()
        sh = gc.open("fantasy_league_db")
        users_df = pd.DataFrame(sh.worksheet("users").get_all_records())
        scores_df = pd.DataFrame(sh.worksheet("rosters").get_all_records())
    except:
        st.error("Database Connection Failed")
        return

    if users_df.empty:
        st.info("No managers registered yet.")
        return

    leaderboard = users_df[['manager_name']].copy()
    leaderboard.columns = ['Manager']
    leaderboard['Total'] = 0.0 
    
    st.dataframe(
        leaderboard, 
        use_container_width=True,
        height=600,
        column_config={
            "Manager": st.column_config.TextColumn("Manager", width="medium"),
            "Total": st.column_config.ProgressColumn("Total Score", format="%.1f", min_value=0, max_value=1000),
        }
    )

# --- 8. WAR ROOM PAGE ---
def war_room_page():
    apply_war_room_style()
    render_navbar()
    
    owner_name = st.session_state['manager_name']
    owner_email = st.session_state['user_email']

    def get_sheet():
        gc = get_connection()
        return gc.open("fantasy_league_db").worksheet("rosters")

    @st.cache_data
    def load_players():
        # UPDATED: Week 4 Player List
        df = pd.read_csv('players_wk4.csv')
        df['name'] = df['name'].astype(str).str.strip() 
        df['display_name'] = df['name'] + " (" + df['team'] + ")"
        return df
        
    @st.cache_data
    def load_multiplier_data():
        # UPDATED: Week 4 Multiplier File
        if os.path.exists("player_mult_wk4.csv"):
            df = pd.read_csv("player_mult_wk4.csv")
            df.columns = df.columns.str.strip().str.lower()
            if 'manager' in df.columns: df['manager'] = df['manager'].astype(str).str.strip()
            if 'player' in df.columns: df['player'] = df['player'].astype(str).str.strip()
            if 'mult' in df.columns: df['mult'] = pd.to_numeric(df['mult'], errors='coerce').fillna(1.0)
            return df
        return pd.DataFrame()

    try: all_players = load_players()
    except: 
        st.error("No players_wk4.csv found")
        st.stop()

    # --- AUTO-LOAD LOGIC ---
    if not st.session_state['roster_loaded']:
        try:
            sheet = get_sheet()
            records = sheet.get_all_records()
            df_cloud = pd.DataFrame(records)
            
            if not df_cloud.empty and 'Manager' in df_cloud.columns and 'Week' in df_cloud.columns:
                mask = (df_cloud['Manager'] == owner_name) & (df_cloud['Week'] == CURRENT_WEEK)
                user_week_data = df_cloud[mask]
                
                if not user_week_data.empty:
                    latest_entry = user_week_data.iloc[-1]
                    cols_to_read = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'FLX1', 'FLX2', 'K', 'DEF']
                    restored_roster = []
                    for c in cols_to_read:
                        if c in latest_entry and latest_entry[c]:
                            restored_roster.append(latest_entry[c])
                    
                    st.session_state['my_roster'] = restored_roster
                    st.toast(f"Week {CURRENT_WEEK} Roster Auto-Loaded", icon="📂")
                else:
                    st.session_state['my_roster'] = []
                    st.toast(f"Welcome to Week {CURRENT_WEEK}. Draft your squad.", icon="⚔️")
            else:
                st.session_state['my_roster'] = []
        except Exception as e:
            st.session_state['my_roster'] = []
        
        st.session_state['roster_loaded'] = True

    # --- CALCULATE MULTIPLIERS (ROBUST MATCHING) ---
    def calculate_multipliers_from_csv(manager):
        mult_map = {}
        mult_df = load_multiplier_data()
        
        if not mult_df.empty:
            if 'manager' not in mult_df.columns:
                return {}
            
            # NORMALIZATION: Lowercase both the logged-in name and the csv column for matching
            target_manager = manager.lower().strip()
            mult_df['manager_clean'] = mult_df['manager'].str.lower().str.strip()
            
            manager_data = mult_df[mult_df['manager_clean'] == target_manager]
            
            if not manager_data.empty:
                mult_map = dict(zip(manager_data['player'], manager_data['mult']))
        
        final_mults = {}
        for name in all_players['name']:
            val = mult_map.get(name, 1.0)
            final_mults[name] = val
        return final_mults

    player_multipliers = calculate_multipliers_from_csv(owner_name)

    # --- SIDEBAR: TEAM ---
    current_roster_names = st.session_state['my_roster']
    
    st.sidebar.markdown("## 🛡️ Current Team")
    st.sidebar.divider()

    roster_slots = {} 
    
    if current_roster_names:
        roster_df = all_players[all_players['name'].isin(current_roster_names)]
        
        qbs = roster_df[roster_df['position'] == 'QB']['name'].tolist()
        rbs = roster_df[roster_df['position'] == 'RB']['name'].tolist()
        wrs = roster_df[roster_df['position'] == 'WR']['name'].tolist()
        tes = roster_df[roster_df['position'] == 'TE']['name'].tolist()
        ks = roster_df[roster_df['position'] == 'K']['name'].tolist()
        defs = roster_df[roster_df['position'] == 'DEF']['name'].tolist()
        
        flex_pool = rbs[2:] + wrs[2:] + tes[1:]
        
        roster_slots['QB'] = qbs[0] if len(qbs) > 0 else ""
        roster_slots['RB1'] = rbs[0] if len(rbs) > 0 else ""
        roster_slots['RB2'] = rbs[1] if len(rbs) > 1 else ""
        roster_slots['WR1'] = wrs[0] if len(wrs) > 0 else ""
        roster_slots['WR2'] = wrs[1] if len(wrs) > 1 else ""
        roster_slots['TE'] = tes[0] if len(tes) > 0 else ""
        roster_slots['FLX1'] = flex_pool[0] if len(flex_pool) > 0 else ""
        roster_slots['FLX2'] = flex_pool[1] if len(flex_pool) > 1 else ""
        roster_slots['K'] = ks[0] if len(ks) > 0 else ""
        roster_slots['DEF'] = defs[0] if len(defs) > 0 else ""

        # VISIBILITY FIX: Custom HTML for Sidebar with Multipliers
        def render_slot_sidebar(label, val):
            display_val = val if val else "---"
            
            # Get multiplier for this specific player
            mult_val = player_multipliers.get(val, 1.0) if val else 1.0
            mult_str = f"{mult_val}x" if val else "-"
            
            # Color code active multipliers
            mult_style = "color: #94A3B8;" # Gray default
            if mult_val > 1.0:
                mult_style = "color: #22c55e; font-weight: 900;" # Bright Green

            st.sidebar.markdown(f"""
            <div style="margin-bottom: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                    <span style="color: #94A3B8; font-size: 11px; font-weight: bold;">{label}</span>
                    <span style="{mult_style} font-size: 11px;">{mult_str}</span>
                </div>
                <div style="background-color: #F1F5F9; color: #111827; padding: 8px; border-radius: 4px; font-weight: 800; font-size: 14px; border: 1px solid #CBD5E1;">
                    {display_val}
                </div>
            </div>
            """, unsafe_allow_html=True)

        render_slot_sidebar("QB", roster_slots['QB'])
        render_slot_sidebar("RB 1", roster_slots['RB1'])
        render_slot_sidebar("RB 2", roster_slots['RB2'])
        render_slot_sidebar("WR 1", roster_slots['WR1'])
        render_slot_sidebar("WR 2", roster_slots['WR2'])
        render_slot_sidebar("TE", roster_slots['TE'])
        render_slot_sidebar("FLEX 1", roster_slots['FLX1'])
        render_slot_sidebar("FLEX 2", roster_slots['FLX2'])
        render_slot_sidebar("K", roster_slots['K'])
        render_slot_sidebar("DEF", roster_slots['DEF'])
        
        count = len(current_roster_names)
        if count == 10: st.sidebar.success(f"{count}/10 Players Selected")
        else: st.sidebar.warning(f"{count}/10 Players Selected")
        
        if len(flex_pool) > 2:
            st.sidebar.error("Too many FLEX players!")

    else:
        st.sidebar.info("Select players from the board.")

    # --- MAIN CONTENT ---
    st.title(f"🏈 {owner_name}'s War Room")
    st.caption(f"Drafting for: **WEEK {CURRENT_WEEK}**")

    # --- LEGEND ---
    st.markdown("""
    <div style="background-color: #1E293B; padding: 12px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 25px; display: flex; justify-content: center; gap: 20px;">
        <span style="color: #E2E8F0; font-weight: bold;">MULTIPLIER KEY:</span>
        <span style="color: #FBBF24; font-weight: bold;">🔥 1.25x</span>
        <span style="color: #F472B6; font-weight: bold;">🚀 1.50x</span>
        <span style="color: #60A5FA; font-weight: bold;">👑 2.00x</span>
    </div>
    """, unsafe_allow_html=True)

    dashboard_placeholder = st.container()
    st.divider()

    # --- TABLES ---
    def render_position_table(position_name, header_text):
        pos_df = all_players[all_players['position'] == position_name].copy()
        
        pos_df['Draft'] = pos_df['name'].isin(st.session_state['my_roster'])
        pos_df['mult'] = pos_df['name'].map(player_multipliers)
        
        def format_name(row):
            base = row['display_name']
            m = row['mult']
            # --- EMOJI FIRST UPDATE ---
            if m == 1.25: return f"🔥 {base}"
            elif m == 1.5: return f"🚀 {base}"
            elif m >= 2.0: return f"👑 {base}"
            else: return base
        
        def format_status(row):
            m = row['mult']
            if m > 1.0: return f"Active ({m}x)"
            return "-"

        pos_df['ui_name'] = pos_df.apply(format_name, axis=1)
        pos_df['status'] = pos_df.apply(format_status, axis=1)
        pos_df = pos_df.sort_values(by=['team', 'name'], ascending=True)
        
        st.subheader(header_text)
        
        # ADDED USE_CONTAINER_WIDTH=TRUE
        edited_df = st.data_editor(
            pos_df[['Draft', 'ui_name', 'status']], 
            key=f"editor_{position_name}", 
            hide_index=True,
            column_config={
                "Draft": st.column_config.CheckboxColumn("Pick", width="small", default=False),
                "ui_name": st.column_config.TextColumn("Player", width="large"),
                "status": st.column_config.TextColumn("Bonus", width="small")
            },
            disabled=["ui_name", "status"], 
            height=450,
            use_container_width=True 
        )
        
        selected_ui_names = edited_df[edited_df['Draft'] == True]['ui_name'].tolist()
        return pos_df[pos_df['ui_name'].isin(selected_ui_names)]['name'].tolist()

    # --- NEW LAYOUT: 2 ROWS of 3 COLUMNS ---
    
    # Row 1: QB, RB, WR
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1: sel_qb = render_position_table("QB", "QB (Pick 1)")
    with r1_c2: sel_rb = render_position_table("RB", "RB (Pick 2-4)")
    with r1_c3: sel_wr = render_position_table("WR", "WR (Pick 2-4)")

    st.write("") # Spacer

    # Row 2: TE, K, DEF
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1: sel_te = render_position_table("TE", "TE (Pick 1-3)")
    with r2_c2: sel_k = render_position_table("K", "K (Pick 1)")
    with r2_c3: sel_def = render_position_table("DEF", "DEF (Pick 1)")

    current_selection = sel_qb + sel_rb + sel_wr + sel_te + sel_k + sel_def
    
    if current_selection != st.session_state['my_roster']:
        st.session_state['my_roster'] = current_selection
        st.rerun()

    # --- DASHBOARD & SAVE ---
    with dashboard_placeholder:
        my_team_data = all_players[all_players['name'].isin(current_selection)].copy()
        
        counts = my_team_data['position'].value_counts().to_dict()
        def get_count(pos): return counts.get(pos, 0)
        qb, rb, wr, te = get_count("QB"), get_count("RB"), get_count("WR"), get_count("TE")
        k, def_ = get_count("K"), get_count("DEF")
        flex = max(0, rb-2) + max(0, wr-2) + max(0, te-1)

        d1, d2, d3 = st.columns([1, 3, 1])
        with d1:
            st.metric("Total Players", f"{len(current_selection)}/10")
        with d2:
            st.write("##### Roster Requirements")
            s1, s2, s3, s4, s5, s6 = st.columns(6)
            s1.markdown(f"**QB**<br>{'✅' if qb==1 else '❌'} {qb}/1", unsafe_allow_html=True)
            s2.markdown(f"**RB**<br>{'✅' if rb>=2 else '⚠️'} {rb}", unsafe_allow_html=True)
            s3.markdown(f"**WR**<br>{'✅' if wr>=2 else '⚠️'} {wr}", unsafe_allow_html=True)
            s4.markdown(f"**TE**<br>{'✅' if te>=1 else '⚠️'} {te}", unsafe_allow_html=True)
            s5.markdown(f"**K**<br>{'✅' if k==1 else '❌'} {k}/1", unsafe_allow_html=True)
            s6.markdown(f"**DEF**<br>{'✅' if def_==1 else '❌'} {def_}/1", unsafe_allow_html=True)
            if flex > 2: st.error(f"Too many Flex! ({flex}/2)")
        with d3:
            if st.button("🔄 Reset Roster", use_container_width=True, type="secondary"):
                st.session_state['my_roster'] = []
                st.rerun()

            valid_roster = (qb==1 and rb>=2 and wr>=2 and te>=1 and flex<=2 and k==1 and def_==1 and len(current_selection)==10)
            if valid_roster:
                if st.button(f"✅ SAVE ROSTER", type="primary", use_container_width=True, key="save_btn", help="save_roster_btn"):
                    with st.spinner("Saving..."):
                        sheet = get_sheet()
                        if sheet:
                            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                            
                            def get_mult(p_name):
                                return player_multipliers.get(p_name, 1.0) if p_name else 1.0

                            row_data = [
                                owner_email,
                                owner_name,
                                ts,
                                CURRENT_WEEK,
                                roster_slots.get('QB', ''),
                                roster_slots.get('RB1', ''),
                                roster_slots.get('RB2', ''),
                                roster_slots.get('WR1', ''),
                                roster_slots.get('WR2', ''),
                                roster_slots.get('TE', ''),
                                roster_slots.get('FLX1', ''),
                                roster_slots.get('FLX2', ''),
                                roster_slots.get('K', ''),
                                roster_slots.get('DEF', ''),
                                get_mult(roster_slots.get('QB')),
                                get_mult(roster_slots.get('RB1')),
                                get_mult(roster_slots.get('RB2')),
                                get_mult(roster_slots.get('WR1')),
                                get_mult(roster_slots.get('WR2')),
                                get_mult(roster_slots.get('TE')),
                                get_mult(roster_slots.get('FLX1')),
                                get_mult(roster_slots.get('FLX2')),
                                get_mult(roster_slots.get('K')),
                                get_mult(roster_slots.get('DEF'))
                            ]
                            
                            sheet.append_row(row_data)
                            st.success(f"Week {CURRENT_WEEK} Saved at {ts} (UTC)")
            else: 
                st.button("Roster Invalid", disabled=True, use_container_width=True)

# --- 9. ROUTER ---
if st.session_state['logged_in']:
    if st.session_state['current_page'] == "War Room":
        war_room_page()
    elif st.session_state['current_page'] == "Leaderboard":
        leaderboard_page()
else:
    login_page()

