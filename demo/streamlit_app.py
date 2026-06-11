import streamlit as st
import requests
import time

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Typing Biometrics Demo", page_icon="🔐", layout="wide")
st.title("🔐 Typing Pattern Authentication")
st.markdown("Authenticate users based on their unique typing patterns.")

if 'enrolled_users' not in st.session_state:
    try:
        response = requests.get(f"{API_URL}/users")
        st.session_state.enrolled_users = response.json().get("users", []) if response.ok else []
    except:
        st.session_state.enrolled_users = []

mode = st.sidebar.radio("Mode", ["Enroll", "Authenticate", "View Users"])

def make_keystrokes(text):
    """Simulate keystroke timing data"""
    keystrokes = []
    for j, c in enumerate(text):
        press = 100 * j + (j * 10)
        release = press + 40 + (j % 3) * 10
        keystrokes.append({'key': c, 'press_time': float(press), 'release_time': float(release)})
    return keystrokes

if mode == "Enroll":
    st.header("👤 Enroll New User")
    user_id = st.text_input("User ID (e.g. lokanshu)")
    phrase = "The quick brown fox jumps over the lazy dog"
    st.info(f"**Type this phrase exactly in all 3 boxes below:**\n\n`{phrase}`")

    s1 = st.text_input("Sample 1", key="s1")
    s2 = st.text_input("Sample 2", key="s2")
    s3 = st.text_input("Sample 3", key="s3")

    if st.button("Enroll"):
        if not user_id:
            st.error("Please enter a User ID")
        elif s1 != phrase or s2 != phrase or s3 != phrase:
            st.warning(f"⚠️ All 3 samples must exactly match the phrase. Check spelling/spaces.")
        else:
            sessions_data = []
            for text in [s1, s2, s3]:
                sessions_data.append({
                    'user_id': user_id,
                    'text': text,
                    'keystrokes': make_keystrokes(text),
                    'session_start': 0.0,
                    'session_end': 5000.0
                })
            try:
                r = requests.post(f"{API_URL}/enroll_typing", 
                                  json={
                                      'user_id': user_id, 
                                      'sessions': sessions_data
                                }
                    )
                
                if r.ok:
                    data = r.json()
                    if data.get('decision') == 'pass':
                        st.success(f"✅ User '{user_id}' enrolled successfully!")
                        st.session_state.enrolled_users.append(user_id)
                    else:
                        st.error(f"❌ Enrollment failed: {data.get('metadata', {})}")
                else:
                    st.error(f"❌ API error {r.status_code}: {r.text}")
            except Exception as e:
                st.error(f"❌ Could not connect to API. Is it running? Error: {e}")

elif mode == "Authenticate":
    st.header("🔓 Authenticate User")
    phrase = "The quick brown fox jumps over the lazy dog"
    st.info(f"**Type this phrase:**\n\n`{phrase}`")

    if not st.session_state.enrolled_users:
        st.warning("No enrolled users yet. Go to Enroll mode first.")
    else:
        user_id = st.selectbox("Select User", st.session_state.enrolled_users)
        text = st.text_input("Type the phrase here")

        if st.button("Authenticate"):
            if text != phrase:
                st.warning("⚠️ Phrase doesn't match exactly.")
            else:
                session = {
                    'user_id': user_id,
                    'text': text,
                    'keystrokes': make_keystrokes(text),
                    'session_start': 0.0,
                    'session_end': 5000.0
                }
                try:
                    r = requests.post(f"{API_URL}/verify", json={'user_id': user_id, 'session': session})
                    if r.ok:
                        res = r.json()
                        confidence = res.get('confidence', 0)
                        decision = res.get('decision', 'fail')
                        if decision == 'pass':
                            st.success(f"✅ AUTHENTICATED! Confidence: {confidence:.1%}")
                        elif decision == 'inconclusive':
                            st.warning(f"⚠️ INCONCLUSIVE. Confidence: {confidence:.1%}")
                        else:
                            st.error(f"❌ FAILED. Confidence: {confidence:.1%}")
                        st.json(res)
                    else:
                        st.error(f"API error: {r.text}")
                except Exception as e:
                    st.error(f"❌ Could not connect to API. Is it running? Error: {e}")

else:
    st.header("📄 Enrolled Users")
    try:
        r = requests.get(f"{API_URL}/users")
        if r.ok:
            data = r.json()
            users = data.get("users", [])
            st.success(f"Total enrolled: {len(users)}")
            for u in users:
                st.write(f"• {u}")
        else:
            st.error("Could not fetch users")
    except:
        st.error("❌ API not running. Start it with: python3 main.py")