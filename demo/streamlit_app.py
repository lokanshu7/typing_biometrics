import streamlit as st
import requests
import json

# Backend endpoint location
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Typing Biometrics Demo", page_icon="🔐", layout="wide")
st.title("🔐 Typing Pattern Authentication")
st.markdown("Authenticate users securely using unique keystroke dynamic patterns.")

# Dynamic session state synchronization for registered usernames
if 'enrolled_users' not in st.session_state:
    try:
        response = requests.get(f"{API_URL}/users")
        if response.ok:
            st.session_state.enrolled_users = response.json().get("users", [])
        else:
            st.session_state.enrolled_users = []
    except:
        st.session_state.enrolled_users = []

mode = st.sidebar.radio("Navigation Menu", ["Enroll New Profile", "Authenticate Profile", "View Registered Users"])

def generate_synthetic_keystrokes(text):
    """
    Simulates high-precision floating point timestamps 
    to fit structural KeystrokeEvent schema requirements
    """
    keystrokes = []
    for j, char in enumerate(text):
        press = 100.0 * j + (j * 12.5)
        # release occurs slightly after press to guarantee positive dwell times
        release = press + 45.0 + (j % 4) * 8.5
        keystrokes.append({
            'key': char, 
            'press_time': float(press), 
            'release_time': float(release)
        })
    return keystrokes

# ==============================================================================
# ENROLL MODE
# ==============================================================================
if mode == "Enroll New Profile":
    st.header("👤 Profile Registration Portal")
    user_id = st.text_input("Enter target Username (min 3 characters):").strip()
    
    phrase = "The quick brown fox jumps over the lazy dog"
    st.info(f"**Type the verification phrase below exactly (Case-Sensitive):**\n\n`{phrase}`")

    s1 = st.text_input("Sample Recording 1", key="s1")
    s2 = st.text_input("Sample Recording 2", key="s2")
    s3 = st.text_input("Sample Recording 3", key="s3")

    if st.button("Submit Registration Profile"):
        if len(user_id) < 3:
            st.error("❌ Username does not meet requirements. Must be at least 3 characters long.")
        elif s1.strip() != phrase or s2.strip() != phrase or s3.strip() != phrase: 
            st.warning("⚠️ Text inputs do not match the required phrase exactly. Verify capitalization or punctuation symbols.")
        else:
            # Constructing list of TypingSession objects containing nested arrays
            sessions_payload = []
            for raw_text in [s1, s2, s3]:
                sessions_payload.append({
                    'user_id': user_id,
                    'text': raw_text.strip(),
                    'keystrokes': generate_synthetic_keystrokes(raw_text.strip()),
                    'session_start': 0.0,
                    'session_end': 6000.0
                })
            
            enrollment_request = {
                'user_id': user_id,
                'sessions': sessions_payload
            }
            
            try:
                with st.spinner("Processing biometric characteristics..."):
                    r = requests.post(f"{API_URL}/enroll_typing", json=enrollment_request)
                
                if r.status_code == 200:
                    data = r.json()
                    if data.get('decision') == 'pass':
                        st.success(f"✅ Secure identity profile for user '{user_id}' has been compiled successfully!")
                        if user_id not in st.session_state.enrolled_users:
                            st.session_state.enrolled_users.append(user_id)
                    else:
                        st.error(f"❌ Rejection handling error: {data.get('metadata', {}).get('reason', 'Unknown parsing error')}")
                else:
                    st.error(f"❌ Backend returned HTTP {r.status_code}: {r.text}")
            except Exception as conn_err:
                st.error(f"❌ Connection dropped or service down. Is your FastAPI engine active? Error: {conn_err}")

# ==============================================================================
# AUTHENTICATE MODE
# ==============================================================================
elif mode == "Authenticate Profile":
    st.header("🔓 Biometric Authentication Entry")
    phrase = "The quick brown fox jumps over the lazy dog"
    st.info(f"**Verify identity by re-typing this baseline phrase:**\n\n`{phrase}`")

    if not st.session_state.enrolled_users:
        st.warning("No registered biometric signatures located locally. Register a user profile via the Enroll tab first.")
    else:
        selected_user = st.selectbox("Identify Username Target", st.session_state.enrolled_users)
        input_string = st.text_input("Input Verification Sequence", key="auth_input")

        if st.button("Analyze Signature"):
            if input_string.strip() != phrase:
                st.warning("⚠️ Provided baseline string doesn't match target metric structure.")
            else:
                authentication_session = {
                    'user_id': selected_user,
                    'text': input_string.strip(),
                    'keystrokes': generate_synthetic_keystrokes(input_string.strip()),
                    'session_start': 0.0,
                    'session_end': 6000.0
                }
                
                auth_request = {
                    'user_id': selected_user,
                    'session': authentication_session
                }
                
                try:
                    with st.spinner("Calculating similarity metrics..."):
                        r = requests.post(f"{API_URL}/verify_typing", json=auth_request)
                    
                    if r.status_code == 200:
                        response_json = r.json()
                        metric_confidence = response_json.get('confidence', 0.0)
                        final_decision = response_json.get('decision', 'fail')
                        
                        if final_decision == 'pass':
                            st.success(f"✅ Identification Verified! Match confidence index parameters hit {metric_confidence:.1%}")
                        elif final_decision == 'inconclusive':
                            st.warning(f"⚠️ Ambiguous Profile Matching. Statistical certainty at {metric_confidence:.1%}")
                        else:
                            st.error(f"❌ Access Denied. Pattern fingerprint variance match failed at {metric_confidence:.1%}")
                        
                        st.write("#### Raw Structural Engine Response Metrics:")
                        st.json(response_json)
                    else:
                        st.error(f"❌ Backend Validation Exception: {r.text}")
                except Exception as conn_err:
                    st.error(f"❌ Connection failure to core platform engine: {conn_err}")

# ==============================================================================
# VIEW REGISTERED USERS
# ==============================================================================
else:
    st.header("📄 Active Biometric Databases")
    try:
        r = requests.get(f"{API_URL}/users")
        if r.status_code == 200:
            user_data = r.json()
            active_list = user_data.get("users", [])
            st.success(f"Successfully connected to directory infrastructure. Total users registered: {len(active_list)}")
            
            if active_list:
                for entry in active_list:
                    st.write(f"🔒 **Enrolled Identity Reference:** `{entry}`")
            else:
                st.info("No signatures stored in active directory path.")
        else:
            st.error(f"Failed to cleanly communicate with identity endpoints. HTTP: {r.status_code}")
    except Exception as service_err:
        st.error(f"❌ Directory reading module isolated. Ensure local server execution via terminal: `python3 -m app.main` or `uvicorn app.main:app` out of root directory space. Log context: {service_err}")