# LANDING PAGE IMAGE LINK:  "https://raw.githubusercontent.com/Lagunis/fantasy-playoff-app/refs/heads/main/football_intro.png"

import streamlit as st
import pandas as pd
import gspread
import hashlib
import os

st.set_page_config(layout="wide", page_title="Champions League")

# --- ⚙️ COMMISSIONER CONTROLS ⚙️ ---
# CHANGE THIS NUMBER (1-4) TO ADVANCE THE LEAGUE WEEK
CURRENT_WEEK = 1 

# --- ⚠️ PASTE YOUR GITHUB IMAGE LINK HERE ⚠️ ---
BACKGROUND_IMAGE_URL = "https://raw.githubusercontent.com/YOUR_USERNAME_HERE/fantasy-playoff-app/main/football_intro.png"

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

         .stApp {{
             background-image: url("{url}");
             background-size: cover;
             background-position: center;
             background-repeat: no-repeat;
             background-attachment: fixed;
         }}
         
         header {{visibility: hidden;}}
         
         /* TITLE CLASS */
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
             background-color: rgba(0, 0, 0, 0.85);
             border: 2px solid #8B0000;
             border-radius: 10px;
             padding: 20px;
             box-shadow: 0 0 30px rgba(139, 0, 0, 0.4);
             color: white;
         }}
         
         div[data-testid="stExpander"] {{
             background-color: rgba(10, 10, 10, 0.98);
             border: 1px solid #8B0000;
             color: white;
         }}
         
         input {{ color: black; }}
         label {{ color: #e0e0e0; }}
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
            background-color: #121212 !important; 
        }
        h1, h2, h3, h4, h5, h6, p, li, div, span {
            color: #E0E0E0 !important; 
        }
        h1, h2, h3 {
            font-family: 'Cinzel', serif !important;
            color: #D22B2B !important; 
            text-shadow: 1px 1px 2px black;
        }
        .stSelectbox div[data-baseweb="select"] > div {
            background-color: #262626 !important; 
            color: white !important;
            border: 1px solid #444;
        }
        [data-testid="stDataEditor"] {
            border: 1px solid #444;
            border-radius: 5px;
            background-color: #1E1E1E;
        }
        [data-testid="stMetricValue"] {
            color: #FFD700 !important; 
            font-size: 36px !important;
        }
        [data-testid="stMetricLabel"] {
            color: #AAAAAA !important;
        }
        button {
            border-radius: 5px !important;
            font-weight: bold !important;
        }
        .streamlit-expanderHeader {
            background-color: #262626 !important;
            color: white !important;
        }
        label[data-baseweb="checkbox"] {
            color: white !important;
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
                return True, user_row['manager_name']
    except Exception as e:
        return False, f"Login Error: {e}"
    return False, "Incorrect email or password."

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'manager_name' not in st.session_state: st.session_state['manager_name'] = ""
if 'my_roster' not in st.session_state: st.session_state['my_roster'] = []
# New: Track if we have already fetched the roster for this session
if 'roster_loaded' not in st.session_state: st.session_state['roster_loaded'] = False

# --- 5. LANDING PAGE ---
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
                is_valid, name = verify_login(email, password)
                if is_valid:
                    st.session_state['logged_in'] = True
                    st.session_state['manager_name'] = name
                    # Reset roster load state on new login
                    st.session_state['roster_loaded'] = False 
                    st.rerun()
                else:
                    st.error(name)
                    
        with tab2:
            new_email = st.text_input("Email", key="signup_email")
            new_user_name = st.text_input("Manager Name", key="signup_name")
            new_password = st.text_input("Password", type='password', key="signup_pass")
            if st.button("SIGN UP", use_container_width=True):
                if new_email and new_password and new_user_name:
                    success, msg = create_user(new_email, new_password, new_user_name)
                    if success: st.success(msg)
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
            * **Objective:** The Manager with the **Highest Cumulative Total Points** at the end of the Super Bowl wins.
            * **Player Pool:** Players are **NOT unique**. Multiple managers can own the same player (e.g., everyone can start Josh Allen).
            * **Weekly Drafting:** You select a fresh lineup every week. You can drop players and pick them back up later freely.
            
            ### 💰 Stakes & Payouts
            * **Entry Fee:** **$50** per manager.
            * **Payout Structure:**
                * If **8+ Managers** join: Top **3 Places** paid.
                * If **< 8 Managers** join: Top **2 Places** paid.
            
            ### 🚀 The Multiplier Strategy
            Loyalty is rewarded. If you start the same player in consecutive weeks, their points are multiplied.
            * **Player's 1st Week:** 100% Points (1.0x)
            * **Player's 2nd Straight Week:** 110% Points (1.1x)
            * **Player's 3rd Straight Week:** 125% Points (1.25x)
            * **Player's 4th Straight Week:** 150% Points (1.5x)
            *(Note: If you bench a player for a week and then bring them back for a later week, the streak resets to 1.0x)*

            ### 📋 Roster Requirements (10 Players)
            | Pos | Count |
            | :--- | :--- |
            | **QB** | 1 |
            | **RB** | 2 |
            | **WR** | 2 |
            | **TE** | 1 |
            | **FLEX** | 2 (RB/WR/TE) |
            | **K** | 1 |
            | **DEF** | 1 (Team Defense) |

            ### 🏈 Scoring Settings
            | Stat | Points |
            | :--- | :--- |
            | **Passing TD** | 6 pts |
            | **2 PT Conversion** | 2 pts |
            | **Passing Yards** | 1 pt per 30 yds |
            | **Interception** | -3 pt |
            | **Pick 6** | -3 pt |
            | **QB Sack Taken** | -1 pt |
            | **Rushing/Rec TD** | 6 pts |
            | **2 PT Conversion** | 2 pts |
            | **Rushing/Rec Yards** | 1 pt per 10 yds |
            | **Reception** | 0.5 pts (Half-PPR) |
            | **Fumble Lost** | -3 pts |
            | **Fumble Rec. TD** | 6 pts |
            | **Safety Taken (Rush/Rec.)** | -2 pts |
            | **Punt Return (Over 10 yards)** | 1 pt per 10 yds |
            | **Kick Return (Over 20 yards)** | 1 pt per 10 yds |
            | **FG Made** | 3 pts |
            | **FGM Yard Over 30** | 0.1 pts |
            | **PAT Made** | 1 pt |
            | **FG Missed** | -3 pts |
            | **PAT Missed** | -3 pts |
            | **Defense TD** | 6 pts |
            | **0 Pts Allowed** | 12 pts |
            | **1-6 Pts Allowed** | 9 pts |
            | **7-13 Pts Allowed** | 6 pts |
            | **14-20 Pts Allowed** | 3 pts |
            | **21-27 Pts Allowed** | 0 pts |
            | **28-34 Pts Allowed** | -3 pts |
            | **35+ Pts Allowed** | -6 pts |
            | **4th Down Stop** | 1 pt |
            | **DEF Sack** | 1 pt |
            | **DEF INT** | 3 pt |
            | **DEF Fumble Recovery** | 3 pt |
            | **Safety** | 5 pt |
            | **Blocked Kick** | 6 pt |
            | **2-PT Conv. Return** | 2 pt |
            """)

# --- 6. MAIN APP ---
def main_game_app():
    apply_war_room_style()
    owner_name = st.session_state['manager_name']

    def get_sheet():
        gc = get_connection()
        return gc.open("fantasy_league_db").sheet1

    @st.cache_data
    def load_players():
        df = pd.read_csv('players.csv')
        df['display_name'] = df['name'] + " (" + df['team'] + ")"
        return df

    try: all_players = load_players()
    except: 
        st.error("No players.csv found")
        st.stop()

    # --- AUTO-LOAD LOGIC ---
    # This runs ONLY ONCE when the user first enters the War Room
    if not st.session_state['roster_loaded']:
        try:
            sheet = get_sheet()
            records = sheet.get_all_records()
            df_cloud = pd.DataFrame(records)
            
            target_col = f"Roster_{CURRENT_WEEK}"
            
            if not df_cloud.empty and owner_name in df_cloud['Manager'].values:
                user_row = df_cloud[df_cloud['Manager'] == owner_name].iloc[0]
                if target_col in user_row and user_row[target_col]:
                    # Found a saved roster for this week!
                    saved_str = user_row[target_col]
                    saved_raw_names = saved_str.split(", ")
                    # Filter to ensure valid names
                    restored_roster = all_players[all_players['name'].isin(saved_raw_names)]['name'].tolist()
                    st.session_state['my_roster'] = restored_roster
                    st.toast(f"Week {CURRENT_WEEK} Roster Auto-Loaded", icon="📂")
                else:
                    # No roster saved yet for this week
                    st.session_state['my_roster'] = []
                    st.toast(f"Welcome to Week {CURRENT_WEEK}. Draft your squad.", icon="⚔️")
            else:
                st.session_state['my_roster'] = []
        except Exception as e:
            st.error(f"Auto-load failed: {e}")
        
        # Mark as loaded so we don't overwrite user changes on next rerun
        st.session_state['roster_loaded'] = True


    # --- HEADER ---
    c1, c2 = st.columns([3, 1])
    with c1: 
        st.title(f"🏈 {owner_name}'s War Room")
        st.caption(f"Drafting for: **WEEK {CURRENT_WEEK}**")
    with c2: 
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.session_state['roster_loaded'] = False
            st.session_state['my_roster'] = []
            st.rerun()

    # --- MULTIPLIERS ---
    def calculate_multipliers(manager, week_num):
        multipliers = {}
        for name in all_players['name']: multipliers[name] = 1.0
        if week_num == 1: return multipliers
        try:
            sheet = get_sheet()
            records = sheet.get_all_records()
            df = pd.DataFrame(records)
            if df.empty or manager not in df['Manager'].values: return multipliers
            user_row = df[df['Manager'] == manager].iloc[0]
            
            def was_in_week(p_name, w):
                col = f"Roster_{w}"
                if col in user_row and user_row[col]: return p_name in user_row[col].split(", ")
                return False
            
            for name in all_players['name']:
                streak = 0
                if was_in_week(name, week_num - 1):
                    streak = 1
                    if week_num > 2 and was_in_week(name, week_num - 2):
                        streak = 2
                        if week_num > 3 and was_in_week(name, week_num - 3): streak = 3
                if streak == 1: multipliers[name] = 1.10
                elif streak == 2: multipliers[name] = 1.25
                elif streak == 3: multipliers[name] = 1.50
        except: pass
        return multipliers

    # Calculate multipliers for CURRENT_WEEK
    player_multipliers = calculate_multipliers(owner_name, CURRENT_WEEK)
    dashboard_placeholder = st.container()
    st.divider()

    # --- TABLES ---
    def render_position_table(position_name, header_text):
        pos_df = all_players[all_players['position'] == position_name].copy()
        if 'my_roster' not in st.session_state: st.session_state['my_roster'] = []
        pos_df['Draft'] = pos_df['name'].isin(st.session_state['my_roster'])
        pos_df['mult'] = pos_df['name'].map(player_multipliers)
        
        def format_name(row):
            base = row['display_name']
            m = row['mult']
            if m == 1.10: return f"{base} ⚡ 1.1x"
            elif m == 1.25: return f"{base} 🔥 1.25x"
            elif m == 1.50: return f"{base} 🚀 1.5x"
            else: return base
        
        def format_status(row):
            m = row['mult']
            if m > 1.0: return f"Active ({int(m*100)}%)"
            return "-"

        pos_df['ui_name'] = pos_df.apply(format_name, axis=1)
        pos_df['status'] = pos_df.apply(format_status, axis=1)
        pos_df = pos_df.sort_values(by=['team', 'name'], ascending=True)
        
        st.subheader(header_text)
        edited_df = st.data_editor(
            pos_df[['Draft', 'ui_name', 'status']], 
            key=f"editor_{position_name}", hide_index=True,
            column_config={
                "Draft": st.column_config.CheckboxColumn("Pick", width="small", default=False),
                "ui_name": st.column_config.TextColumn("Player", width="large"),
                "status": st.column_config.TextColumn("Bonus", width="small")
            },
            disabled=["ui_name", "status"], height=450
        )
        selected_ui_names = edited_df[edited_df['Draft'] == True]['ui_name'].tolist()
        return pos_df[pos_df['ui_name'].isin(selected_ui_names)]['name'].tolist()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: sel_qb = render_position_table("QB", "QB (Pick 1)")
    with c2: sel_rb = render_position_table("RB", "RB (Pick 2-4)")
    with c3: sel_wr = render_position_table("WR", "WR (Pick 2-4)")
    with c4: sel_te = render_position_table("TE", "TE (Pick 1-3)")
    with c5: sel_k = render_position_table("K", "K (Pick 1)")
    with c6: sel_def = render_position_table("DEF", "DEF (Pick 1)")

    current_selection = sel_qb + sel_rb + sel_wr + sel_te + sel_k + sel_def
    st.session_state['my_roster'] = current_selection

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
            valid_roster = (qb==1 and rb>=2 and wr>=2 and te>=1 and flex<=2 and k==1 and def_==1 and len(current_selection)==10)
            if valid_roster:
                if st.button(f"💾 Submit Week {CURRENT_WEEK}", type="primary", use_container_width=True, key="save_btn"):
                    with st.spinner("Saving..."):
                        sheet = get_sheet()
                        if sheet:
                            raw_names = my_team_data['name'].tolist()
                            roster_str = ", ".join(raw_names)
                            records = sheet.get_all_records()
                            df_cloud = pd.DataFrame(records)
                            
                            # Ensure manager exists
                            if df_cloud.empty or owner_name not in df_cloud['Manager'].values:
                                new_row = {"Manager": owner_name}
                                df_cloud = pd.concat([df_cloud, pd.DataFrame([new_row])], ignore_index=True)
                            
                            idx = df_cloud.index[df_cloud['Manager'] == owner_name].tolist()[0]
                            
                            # Save to CURRENT_WEEK column
                            df_cloud.at[idx, f'Roster_{CURRENT_WEEK}'] = roster_str
                            df_cloud.at[idx, f'Points_{CURRENT_WEEK}'] = 0 
                            
                            sheet.clear()
                            sheet.update([df_cloud.columns.values.tolist()] + df_cloud.values.tolist())
                            st.success(f"Week {CURRENT_WEEK} Saved!")
            else: st.button("Roster Invalid", disabled=True, use_container_width=True)

# --- 7. ROUTER ---
if st.session_state['logged_in']: main_game_app()
else: login_page()
