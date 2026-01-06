# LANDING PAGE IMAGE LINK:  "https://raw.githubusercontent.com/Lagunis/fantasy-playoff-app/refs/heads/main/football_intro.png"

import streamlit as st
import pandas as pd
import gspread
import hashlib
import os

st.set_page_config(layout="wide", page_title="Champions League")

# --- ⚙️ COMMISSIONER CONTROLS ⚙️ ---
CURRENT_WEEK = 1 

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
         
         /* LANDING PAGE TITLE */
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

         /* LANDING PAGE LOGIN BOX */
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
         
         /* LANDING PAGE INPUTS */
         label {{ color: white !important; }}
         input {{ color: black !important; }}

         /* RULES BOX FIXES */
         /* Force the expander background to be dark */
         div[data-testid="stExpander"] {{
             background-color: #0F172A !important;
             border: 1px solid #8B0000 !important;
             color: white !important;
         }}
         div[data-testid="stExpander"] p, li, span, div {{
            color: #E2E8F0 !important;
         }}
         /* Hide the weird "keyboard_arrow_down" text artifact */
         div[data-testid="stExpander"] summary span {{
             display: none !important; 
         }}
         /* Re-add a manual arrow if needed, but usually clicking the box works fine */
         
         /* LOGIN / SIGNUP BUTTONS */
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
        
        /* SIDEBAR INPUTS: FIXED TO BE DARK GRAY */
        div[data-testid="stSidebar"] input {
            color: #111827 !important; /* Almost Black */
            font-weight: 900 !important; /* Extra Bold */
            background-color: #F1F5F9 !important; /* Light Grey Background */
            -webkit-text-fill-color: #111827 !important; /* Force override for Webkit */
            opacity: 1 !important; /* Ensure no transparency */
        }
        
        /* LOGOUT BUTTON */
        button[kind="secondary"] {
            background-color: #7F1D1D !important;
            color: white !important;
            border: 1px solid #EF4444 !important;
        }

        /* SAVE ROSTER BUTTON */
        button[kind="primary"] {
            background-color: #15803d !important; 
            color: white !important;
            border: 1px solid #4ade80 !important;
            font-size: 18px !important;
        }
        
        /* NAV BAR BUTTONS */
        /* We create a special class of buttons for navigation */
        div[data-testid="stHorizontalBlock"] button {
            border: 1px solid #334155;
        }

        /* Tables */
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
                return True, user_row['manager_name']
    except Exception as e:
        return False, f"Login Error: {e}"
    return False, "Incorrect email or password."

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'manager_name' not in st.session_state: st.session_state['manager_name'] = ""
if 'my_roster' not in st.session_state: st.session_state['my_roster'] = []
if 'roster_loaded' not in st.session_state: st.session_state['roster_loaded'] = False
if 'current_page' not in st.session_state: st.session_state['current_page'] = "War Room" # Track which page we are on

# --- 5. PAGE NAVIGATION COMPONENT ---
def render_navbar():
    """Renders the top navigation to switch between pages"""
    c1, c2, c3, c4 = st.columns([1, 1, 4, 1])
    
    with c1:
        # If button clicked, change state to War Room
        if st.button("⚔️ WAR ROOM", use_container_width=True, type="primary" if st.session_state['current_page'] == "War Room" else "secondary"):
            st.session_state['current_page'] = "War Room"
            st.rerun()
            
    with c2:
        # If button clicked, change state to Leaderboard
        if st.button("🏛️ COLOSSEUM", use_container_width=True, type="primary" if st.session_state['current_page'] == "Leaderboard" else "secondary"):
            st.session_state['current_page'] = "Leaderboard"
            st.rerun()
            
    with c4:
        if st.button("LOG OUT", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.session_state['roster_loaded'] = False
            st.session_state['my_roster'] = []
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
                is_valid, name = verify_login(email, password)
                if is_valid:
                    st.session_state['logged_in'] = True
                    st.session_state['manager_name'] = name
                    st.session_state['roster_loaded'] = False 
                    st.rerun()
                else:
                    st.error(name)
                    
        with tab2:
            new_email = st.text_input("Email", key="signup_email")
            new_user_name = st.text_input("Manager Name", key="signup_name")
            new_password = st.text_input("Password", type='password', key="signup_pass")
            # AUTO-LOGIN LOGIC ADDED HERE
            if st.button("SIGN UP", use_container_width=True, type="primary"):
                if new_email and new_password and new_user_name:
                    success, msg = create_user(new_email, new_password, new_user_name)
                    if success: 
                        st.success(msg)
                        # Auto-Login
                        st.session_state['logged_in'] = True
                        st.session_state['manager_name'] = new_user_name
                        st.session_state['roster_loaded'] = False
                        st.rerun()
                    else: st.error(msg)
                else:
                    st.warning("Missing info")

    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    c_left, c_center, c_right = st.columns([1, 2, 1])
    with c_center:
        with st.expander("📜 RULES OF THE ARENA (Read Carefully)", expanded=False):
            if os.path.exists("rules.md"):
                with open("rules.md", "r") as f:
                    rules_text = f.read()
                st.markdown(rules_text)
            else:
                st.warning("rules.md file not found.")

# --- 7. LEADERBOARD PAGE ("THE COLOSSEUM") ---
def leaderboard_page():
    apply_war_room_style()
    render_navbar()
    
    st.title("🏛️ The Colosseum")
    st.caption("Current Standings & Manager Directory")
    
    # Fetch Data
    try:
        gc = get_connection()
        sh = gc.open("fantasy_league_db")
        # Get users
        users_df = pd.DataFrame(sh.worksheet("users").get_all_records())
        # Get scores
        scores_df = pd.DataFrame(sh.sheet1.get_all_records())
    except:
        st.error("Database Connection Failed")
        return

    if users_df.empty:
        st.info("No managers registered yet.")
        return

    # Build the Leaderboard Table
    # Start with all registered managers
    leaderboard = users_df[['manager_name']].copy()
    leaderboard.columns = ['Manager']
    
    # Initialize Score Columns
    leaderboard['Week 1'] = 0.0
    leaderboard['Week 2'] = 0.0
    leaderboard['Week 3'] = 0.0
    leaderboard['Week 4'] = 0.0
    leaderboard['Total'] = 0.0
    
    # If we have score data, map it
    if not scores_df.empty:
        for idx, row in leaderboard.iterrows():
            mgr = row['Manager']
            if mgr in scores_df['Manager'].values:
                score_row = scores_df[scores_df['Manager'] == mgr].iloc[0]
                # Safely get points or default to 0
                w1 = float(score_row.get('Points_1', 0) or 0)
                w2 = float(score_row.get('Points_2', 0) or 0)
                w3 = float(score_row.get('Points_3', 0) or 0)
                w4 = float(score_row.get('Points_4', 0) or 0)
                
                leaderboard.at[idx, 'Week 1'] = w1
                leaderboard.at[idx, 'Week 2'] = w2
                leaderboard.at[idx, 'Week 3'] = w3
                leaderboard.at[idx, 'Week 4'] = w4
                leaderboard.at[idx, 'Total'] = w1 + w2 + w3 + w4

    # Sort by Total Points
    leaderboard = leaderboard.sort_values(by='Total', ascending=False).reset_index(drop=True)
    leaderboard.index += 1 # Rank starts at 1
    
    st.dataframe(
        leaderboard, 
        use_container_width=True,
        height=600,
        column_config={
            "Manager": st.column_config.TextColumn("Manager", width="medium"),
            "Week 1": st.column_config.NumberColumn("Week 1", format="%.1f"),
            "Week 2": st.column_config.NumberColumn("Week 2", format="%.1f"),
            "Week 3": st.column_config.NumberColumn("Week 3", format="%.1f"),
            "Week 4": st.column_config.NumberColumn("Week 4", format="%.1f"),
            "Total": st.column_config.ProgressColumn(
                "Total Score", 
                format="%.1f", 
                min_value=0, 
                max_value=1000 # Estimate max score for bar scaling
            ),
        }
    )

# --- 8. WAR ROOM PAGE ---
def war_room_page():
    apply_war_room_style()
    render_navbar()
    
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
    if not st.session_state['roster_loaded']:
        try:
            sheet = get_sheet()
            records = sheet.get_all_records()
            df_cloud = pd.DataFrame(records)
            
            target_col = f"Roster_{CURRENT_WEEK}"
            
            if not df_cloud.empty and owner_name in df_cloud['Manager'].values:
                user_row = df_cloud[df_cloud['Manager'] == owner_name].iloc[0]
                if target_col in user_row and user_row[target_col]:
                    saved_str = user_row[target_col]
                    saved_raw_names = saved_str.split(", ")
                    restored_roster = all_players[all_players['name'].isin(saved_raw_names)]['name'].tolist()
                    st.session_state['my_roster'] = restored_roster
                    st.toast(f"Week {CURRENT_WEEK} Roster Auto-Loaded", icon="📂")
                else:
                    st.session_state['my_roster'] = []
                    st.toast(f"Welcome to Week {CURRENT_WEEK}. Draft your squad.", icon="⚔️")
            else:
                st.session_state['my_roster'] = []
        except Exception as e:
            st.error(f"Auto-load failed: {e}")
        
        st.session_state['roster_loaded'] = True

    # --- SIDEBAR: CURRENT TEAM DISPLAY ---
    current_roster_names = st.session_state['my_roster']
    if current_roster_names:
        roster_df = all_players[all_players['name'].isin(current_roster_names)]
        
        qbs = roster_df[roster_df['position'] == 'QB']['display_name'].tolist()
        rbs = roster_df[roster_df['position'] == 'RB']['display_name'].tolist()
        wrs = roster_df[roster_df['position'] == 'WR']['display_name'].tolist()
        tes = roster_df[roster_df['position'] == 'TE']['display_name'].tolist()
        ks = roster_df[roster_df['position'] == 'K']['display_name'].tolist()
        defs = roster_df[roster_df['position'] == 'DEF']['display_name'].tolist()
        
        flex_pool = rbs[2:] + wrs[2:] + tes[1:] 
        
        st.sidebar.markdown("## 🛡️ Current Team")
        st.sidebar.divider()
        
        def render_slot(label, players, index):
            val = players[index] if len(players) > index else "---"
            st.sidebar.text_input(label, val, disabled=True, key=f"slot_{label}_{index}_{val}")

        render_slot("QB", qbs, 0)
        render_slot("RB 1", rbs, 0)
        render_slot("RB 2", rbs, 1)
        render_slot("WR 1", wrs, 0)
        render_slot("WR 2", wrs, 1)
        render_slot("TE", tes, 0)
        
        f1 = flex_pool[0] if len(flex_pool) > 0 else "---"
        f2 = flex_pool[1] if len(flex_pool) > 1 else "---"
        
        st.sidebar.text_input("FLEX 1", f1, disabled=True, key=f"flex_1_{f1}")
        st.sidebar.text_input("FLEX 2", f2, disabled=True, key=f"flex_2_{f2}")
        
        render_slot("K", ks, 0)
        render_slot("DEF", defs, 0)
        
        count = len(current_roster_names)
        if count == 10: st.sidebar.success(f"{count}/10 Players Selected")
        else: st.sidebar.warning(f"{count}/10 Players Selected")
        
        if len(flex_pool) > 2:
            st.sidebar.error("Too many FLEX players!")

    else:
        st.sidebar.markdown("## 🛡️ Current Team")
        st.sidebar.info("Select players from the board.")

    # --- TITLE ---
    st.title(f"🏈 {owner_name}'s War Room")
    st.caption(f"Drafting for: **WEEK {CURRENT_WEEK}**")

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

    player_multipliers = calculate_multipliers(owner_name, CURRENT_WEEK)
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
            key=f"editor_{position_name}", 
            hide_index=True,
            column_config={
                "Draft": st.column_config.CheckboxColumn("Pick", width="small", default=False),
                "ui_name": st.column_config.TextColumn("Player", width="large"),
                "status": st.column_config.TextColumn("Bonus", width="small")
            },
            disabled=["ui_name", "status"], 
            height=450
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
    
    # UPDATE STATE INSTANTLY
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
            valid_roster = (qb==1 and rb>=2 and wr>=2 and te>=1 and flex<=2 and k==1 and def_==1 and len(current_selection)==10)
            if valid_roster:
                if st.button(f"✅ SAVE ROSTER", type="primary", use_container_width=True, key="save_btn"):
                    with st.spinner("Saving..."):
                        sheet = get_sheet()
                        if sheet:
                            raw_names = my_team_data['name'].tolist()
                            roster_str = ", ".join(raw_names)
                            records = sheet.get_all_records()
                            df_cloud = pd.DataFrame(records)
                            
                            if df_cloud.empty or owner_name not in df_cloud['Manager'].values:
                                new_row = {"Manager": owner_name}
                                df_cloud = pd.concat([df_cloud, pd.DataFrame([new_row])], ignore_index=True)
                            
                            idx = df_cloud.index[df_cloud['Manager'] == owner_name].tolist()[0]
                            
                            df_cloud.at[idx, f'Roster_{CURRENT_WEEK}'] = roster_str
                            df_cloud.at[idx, f'Points_{CURRENT_WEEK}'] = 0 
                            
                            sheet.clear()
                            sheet.update([df_cloud.columns.values.tolist()] + df_cloud.values.tolist())
                            st.success(f"Week {CURRENT_WEEK} Saved!")
            else: st.button("Roster Invalid", disabled=True, use_container_width=True)

# --- 9. ROUTER ---
if st.session_state['logged_in']:
    if st.session_state['current_page'] == "War Room":
        war_room_page()
    elif st.session_state['current_page'] == "Leaderboard":
        leaderboard_page()
else:
    login_page()
