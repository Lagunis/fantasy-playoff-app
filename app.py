import streamlit as st
import pandas as pd
import gspread

# We need "wide" mode for 6 columns to fit comfortably!
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
    # Make sure players.csv is in your GitHub repo!
    return pd.read_csv('players.csv')

try:
    all_players = load_players()
    if 'Draft' not in all_players.columns:
        all_players['Draft'] = False
except:
    st.error("CRITICAL ERROR: Could not find players.csv")
    st.stop()

if 'my_roster' not in st.session_state:
    st.session_state['my_roster'] = []

# --- 2. HEADER & LOGIN ---
st.title("🏈 The Draft Board")

# Create a container for the login controls to keep them tidy
with st.expander("Manager Login & Tools", expanded=True):
    col_login, col_btn = st.columns([3, 1])
    with col_login:
        owner_name = st.text_input("Manager Name", "User 1")
    with col_btn:
        st.write("") # Spacer
        if st.button("📂 Load Saved Roster"):
            try:
                sheet = get_sheet()
                records = sheet.get_all_records()
                df_cloud = pd.DataFrame(records)
                
                if not df_cloud.empty and owner_name in df_cloud['Manager'].values:
                    saved_str = df_cloud.loc[df_cloud['Manager'] == owner_name, 'Roster'].iloc[0]
                    st.session_state['my_roster'] = saved_str.split(", ")
                    st.toast(f"Roster loaded for {owner_name}!", icon="✅")
                    st.rerun()
                else:
                    st.toast("No saved team found.", icon="⚠️")
            except:
                st.error("Connection failed.")

# --- 3. THE DRAFT BOARD HELPER ---
def render_position_table(position_name, limit):
    pos_df = all_players[all_players['position'] == position_name].copy()
    pos_df['Draft'] = pos_df['name'].isin(st.session_state['my_roster'])
    
    # Sort: Selected players first, then by points
    pos_df = pos_df.sort_values(by=['Draft', 'projected_points'], ascending=[False, False])
    
    # Header showing limits
    st.markdown(f"**{position_name}** (Pick {limit})")
    
    # COMPACT TABLE CONFIGURATION
    edited_df = st.data_editor(
        pos_df[['Draft', 'name', 'projected_points']], # Removed 'Team' to save space
        key=f"editor_{position_name}",
        hide_index=True,
        column_config={
            "Draft": st.column_config.CheckboxColumn(
                "Pick",
                width="small",
                default=False,
            ),
            "name": st.column_config.TextColumn(
                "Player",
                width="medium", # Give name the most space
            ),
            "projected_points": st.column_config.NumberColumn(
                "Pts",
                format="%.1f",
                width="small"
            )
        },
        disabled=["name", "projected_points"],
        height=400 # Taller to see more players
    )
    
    return edited_df[edited_df['Draft'] == True]['name'].tolist()

# --- 4. THE 6-COLUMN LAYOUT ---
# We create 6 equal columns
c1, c2, c3, c4, c5, c6 = st.columns(6)

# Assign positions to columns
with c1:
    sel_qb = render_position_table("QB", 1)
with c2:
    sel_rb = render_position_table("RB", 2)
with c3:
    sel_wr = render_position_table("WR", 2)
with c4:
    sel_te = render_position_table("TE", 1)
with c5:
    sel_k = render_position_table("K", 1)
with c6:
    sel_def = render_position_table("DEF", 1)

# Combine selections
current_selection = sel_qb + sel_rb + sel_wr + sel_te + sel_k + sel_def
st.session_state['my_roster'] = current_selection

# --- 5. SIDEBAR: SCOREBOARD & SAVE ---
st.sidebar.header(f"📋 Ticket: {owner_name}")

if current_selection:
    my_team_data = all_players[all_players['name'].isin(current_selection)]
    total_pts = my_team_data['projected_points'].sum()
    
    # Big Score Display
    st.sidebar.metric("Projected Total", f"{total_pts:.2f}")
    
    # List of selected players
    st.sidebar.dataframe(
        my_team_data[['name', 'position']], 
        hide_index=True,
        use_container_width=True
    )
    
    # Validation
    counts = my_team_data['position'].value_counts().to_dict()
    def get_count(pos): return counts.get(pos, 0)
    
    qb = get_count("QB")
    rb = get_count("RB")
    wr = get_count("WR")
    te = get_count("TE")
    k  = get_count("K")
    def_ = get_count("DEF")
    
    # Flex Logic
    flex = max(0, rb-2) + max(0, wr-2) + max(0, te-1)
    
    st.sidebar.divider()
    st.sidebar.caption("Requirements:")
    
    # Use simple icons for valid/invalid
    st.sidebar.write(f"{'✅' if qb==1 else '❌'} QB: {qb}/1")
    st.sidebar.write(f"{'✅' if rb>=2 else '❌'} RB: {rb}/2+")
    st.sidebar.write(f"{'✅' if wr>=2 else '❌'} WR: {wr}/2+")
    st.sidebar.write(f"{'✅' if te>=1 else '❌'} TE: {te}/1+")
    st.sidebar.write(f"{'✅' if flex<=2 else '❌'} FLEX: {flex}/2")
    st.sidebar.write(f"{'✅' if k==1 else '❌'} K: {k}/1")
    st.sidebar.write(f"{'✅' if def_==1 else '❌'} DEF: {def_}/1")
    
    valid_roster = (qb==1 and rb>=2 and wr>=2 and te>=1 and flex<=2 and k==1 and def_==1 and len(current_selection)==10)
    
    if valid_roster:
        if st.sidebar.button("💾 Submit Roster", type="primary"):
            with st.spinner("Submitting..."):
                sheet = get_sheet()
                if sheet:
                    roster_str = ", ".join(current_selection)
                    records = sheet.get_all_records()
                    df_cloud = pd.DataFrame(records)
                    
                    new_row = {"Manager": owner_name, "Roster": roster_str, "Points": total_pts}
                    
                    if not df_cloud.empty and 'Manager' in df_cloud.columns:
                        df_cloud = df_cloud[df_cloud['Manager'] != owner_name]
                    
                    df_cloud = pd.concat([df_cloud, pd.DataFrame([new_row])], ignore_index=True)
                    sheet.clear()
                    sheet.update([df_cloud.columns.values.tolist()] + df_cloud.values.tolist())
                    st.sidebar.success("Saved!")
    else:
        st.sidebar.warning(f"Roster Incomplete ({len(current_selection)}/10)")

else:
    st.sidebar.info("Select players to begin.")
