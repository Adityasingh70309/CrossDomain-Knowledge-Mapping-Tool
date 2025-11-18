import streamlit as st
import requests
import os
import csv

BACKEND_URL = "http://127.0.0.1:5000"


def load_css(file_name="style.css"):
    try:
        base_dir = os.path.dirname(__file__)
        candidates = [
            os.path.join(base_dir, file_name),
            os.path.join(base_dir, "..", file_name),
        ]
        for path in candidates:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
                return
        st.warning(f"CSS file '{file_name}' not found near {base_dir}")
    except Exception as e:
        st.warning(f"CSS Load Error: {e}")


st.markdown("# 📝 Feedback")
load_css()

if "jwt_token" not in st.session_state or not st.session_state.get("jwt_token"):
    st.info("Please sign in to submit feedback.")
    st.stop()

fb_type = st.selectbox("Feedback Type", ["Bug", "Suggestion", "Data Issue", "Other"])
fb_text = st.text_area("Your feedback", height=200)

if st.button("Submit Feedback", type="primary"):
    if not fb_text or not fb_text.strip():
        st.warning("Please enter feedback text.")
    else:
        token = st.session_state.get("jwt_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"type": fb_type, "text": fb_text}
        try:
            r = requests.post(f"{BACKEND_URL}/submit_feedback", json=payload, headers=headers, timeout=10)
            if r.status_code in (200, 201):
                st.success("Feedback submitted. Thank you!")
            else:
                st.warning(f"Server responded with {r.status_code}: {r.text}. Falling back to local save.")
                raise Exception("Server error")
        except Exception:
            # Fallback: save to local CSV
            local_path = os.path.join(os.path.dirname(__file__), '..', 'feedback_local.csv')
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            write_header = not os.path.exists(local_path)
            with open(local_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(['user', 'type', 'text'])
                user = st.session_state.get('user_email') or st.session_state.get('jwt_token')[:8]
                writer.writerow([user, fb_type, fb_text.replace('\n', ' ')])
            st.success(f"Saved feedback locally to {local_path}")
