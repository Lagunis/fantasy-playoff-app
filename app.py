import streamlit as st
import pandas as pd
import gspread

st.set_page_config(layout="wide", page_title="Playoff Fantasy")

# --- 1. SETUP & CONNECTIONS ---
def get_sheet():
    if "gcp_service_account" not in st.secrets:
        st.error("Secrets not found!")
        return None
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("fantasy_league_db")
    return sh.sheet1

@st.cache_data
def load_players():
    df = pd.read_csv('players.csv')
    df['display_name'] = df['name'] + " (" + df['team'] + ")"
    return df

try:
    all_players = load_players()
except:
    st.error("CRITICAL ERROR: Could not find players.csv")
    st.stop()

if 'my_roster' not in st.session_state:
    st.session_state['my_roster'] = []

# --- 2. HEADER & CONFIGURATION ---
st.title("🏈 Playoff Draft Board")

# Top Control Bar
with st.expander("League Settings & Login", expanded=True):
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        owner_name = st.text_input("Manager Name", "User 1")
    
    with c2:
        # NEW: Week Selector
        current_week = st.selectbox("Current Week", [1, 2, 3, 4])
        
    with c3:
        st.write("") 
        if st.button("📂 Load Saved Roster"):
            try:
                sheet = get_sheet()
                records = sheet.get_all_records()
                df_cloud = pd.DataFrame(records)
                
                # Check if manager exists
                if not df_cloud.empty and owner_name in df_cloud['Manager'].values:
                    # Load the specific roster column for this week (e.g., 'Roster_2')
                    target_col = f"Roster_{current_week}"
                    user_row = df_cloud[df_cloud['Manager'] == owner_name].iloc[0]
                    
                    if target_col in user_row and user_row[target_col]:
                        saved_str = user_row[target_col]
                        saved_raw_names = saved_str.split(", ")
                        restored_roster = all_players[all_players['name'].isin(saved_raw_names)]['display_name'].tolist()
                        st.session_state['my_roster'] = restored_roster
                        st.toast(f"Week {current_week} Roster Loaded!", icon="✅")
                        st.rerun()
                    else:
                        st.toast(f"No roster found for Week {current_week}.", icon="ℹ️")
                        st.session_state['my_roster'] = [] # Reset if empty for this week
                        st.rerun()
                else:
                    st.toast("User not found.", icon="⚠️")
            except Exception as e:
                st.error(f"Connection failed: {e}")

# --- 3. MULTIPLIER LOGIC ENGINE ---
def calculate_multipliers(manager, week_num):
    """
    Returns a dictionary: { 'Player Name (Team)': 1.25 }
    Based on previous weeks' rosters from Google Sheets.
    """
    multipliers = {}
    default_mult = 1.0
    
    # Initialize everyone at 1.0
    for p in all_players['display_name']:
        multipliers[p] = default_mult

    if week_num == 1:
        return multipliers # No bonuses in Week 1

    # Fetch history
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        
        if df.empty or manager not in df['Manager'].values:
            return multipliers # No history found
            
        user_row = df[df['Manager'] == manager].iloc[0]
        
        # Helper to check if player was in a specific past week
        def was_in_week(p_name_raw, w):
            col = f"Roster_{w}"
            if col in user_row and user_row[col]:
                return p_name_raw in user_row[col].split(", ")
            return False

        # Loop through all players and calculate their specific bonus
        for _, row in all_players.iterrows():
            raw_name = row['name']
            disp_name = row['display_name']
            
            # Logic: Check Streak backwards from current week
            streak = 0
            
            # Check Week (Current - 1)
            if was_in_week(raw_name, week_num - 1):
                streak = 1
                # Check Week (Current - 2)
                if week_num > 2 and was_in_week(raw_name, week_num - 2):
                    streak = 2
                    # Check Week (Current - 3)
                    if week_num > 3 and was_in_week(raw_name, week_num - 3):
                        streak = 3
            
            # Assign Multiplier based on streak
            if streak == 1: multipliers[disp_name] = 1.10  # 110%
            elif streak == 2: multipliers[disp_name] = 1.25 # 125%
            elif streak == 3: multipliers[disp_name] = 1.50 # 150%
            
    except Exception as e:
        print(f"Error calculating multipliers: {e}")
        
    return multipliers

# Calculate bonuses for the CURRENT user state
# We only do this once per rerun to save time
player_multipliers = calculate_multipliers(owner_name, current_week)

# --- 4. RESERVE SPACE FOR DASHBOARD ---
dashboard_placeholder = st.container()

st.divider()

# --- 5. RENDER TABLES ---
def render_position_table(position_name, header_text):
    pos_df = all_players[all_players['position'] == position_name].copy()
    
    # Check boxes
    pos_df['Draft'] = pos_df['display_name'].isin(st.session_state['my_roster'])
    
    # --- APPLY MULTIPLIERS ---
    # We map the multiplier dict to the dataframe
    pos_df['mult'] = pos_df['display_name'].map(player_multipliers)
    
    # Calculate "Boosted Points"
    pos_df['boosted_points'] = pos_df['projected_points'] * pos_df['mult']
    
    # Create a nice label string: "22.5 (1.1x)"
    pos_df['display_pts'] = pos_df.apply(
        lambda x: f"{x['boosted_points']:.1f} ({int(x['mult']*100)}%)" if x['mult'] > 1.0 else f"{x['boosted_points']:.1f}", 
        axis=1
    )

    # Sort by BOOSTED points
    pos_df = pos_df.sort_values(by=['boosted_points'], ascending=False)
    
    st.subheader(header_text)
    
    edited_df = st.data_editor(
        pos_df[['Draft', 'display_name', 'display_pts']], 
        key=f"editor_{position_name}",
        hide_index=True,
        column_config={
            "Draft": st.column_config.CheckboxColumn("Pick", width="small", default=False),
            "display_name": st.column_config.TextColumn("Player", width="large"),
            "display_pts": st.column_config.TextColumn("Pts (Bonus)", width="small") # Changed to Text to show "22.5 (110%)"
        },
        disabled=["display_name", "display_pts"],
        height=450
    )
    
    return edited_df[edited_df['Draft'] == True]['display_name'].tolist()

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1: sel_qb = render_position_table("QB", "QB (Pick 1)")
with c2: sel_rb = render_position_table("RB", "RB (Pick 2-4)")
with c3: sel_wr = render_position_table("WR", "WR (Pick 2-4)")
with c4: sel_te = render_position_table("TE", "TE (Pick 1-3)")
with c5: sel_k = render_position_table("K", "K (Pick 1)")
with c6: sel_def = render_position_table("DEF", "DEF (Pick 1)")

current_selection = sel_qb + sel_rb + sel_wr + sel_te + sel_k + sel_def
st.session_state['my_roster'] = current_selection

# --- 6. FILL DASHBOARD ---
with dashboard_placeholder:
    my_team_data = all_players[all_players['display_name'].isin(current_selection)].copy()
    
    # Recalculate total with bonuses
    my_team_data['mult'] = my_team_data['display_name'].map(player_multipliers)
    my_team_data['boosted_points'] = my_team_data['projected_points'] * my_team_data['mult']
    total_pts = my_team_data['boosted_points'].sum()
    
    counts = my_team_data['position'].value_counts().to_dict()
    def get_count(pos): return counts.get(pos, 0)
    qb, rb, wr, te = get_count("QB"), get_count("RB"), get_count("WR"), get_count("TE")
    k, def_ = get_count("K"), get_count("DEF")
    flex = max(0, rb-2) + max(0, wr-2) + max(0, te-1)

    d1, d2, d3 = st.columns([1, 3, 1])
    
    with d1:
        st.metric("Projected Score", f"{total_pts:.1f}")
        if current_week > 1:
            st.caption(f"Includes Week {current_week} Streak Bonuses")
        st.write(f"**Players:** {len(current_selection)}/10")
        
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
            if st.button(f"💾 Submit Week {current_week}", type="primary", use_container_width=True, key="save_btn"):
                with st.spinner("Saving..."):
                    sheet = get_sheet()
                    if sheet:
                        raw_names = my_team_data['name'].tolist()
                        roster_str = ", ".join(raw_names)
                        
                        records = sheet.get_all_records()
                        df_cloud = pd.DataFrame(records)
                        
                        # Prepare the updated data for this specific week
                        # We try to find the user, if not found, we create them
                        if df_cloud.empty or owner_name not in df_cloud['Manager'].values:
                            new_row = {"Manager": owner_name}
                            df_cloud = pd.concat([df_cloud, pd.DataFrame([new_row])], ignore_index=True)
                        
                        # Find the index of the manager
                        idx = df_cloud.index[df_cloud['Manager'] == owner_name].tolist()[0]
                        
                        # Update the specific columns for this week
                        # Note: We must update the DataFrame logic carefully
                        df_cloud.at[idx, f'Roster_{current_week}'] = roster_str
                        df_cloud.at[idx, f'Points_{current_week}'] = total_pts
                        
                        # Write back
                        sheet.clear()
                        # Ensure headers are preserved? get_all_records usually handles keys well
                        # Re-uploading the whole dataframe is safest for MVP
                        sheet.update([df_cloud.columns.values.tolist()] + df_cloud.values.tolist())
                        st.success(f"Week {current_week} Saved!")
        else:
            st.button("Roster Invalid", disabled=True, use_container_width=True)
