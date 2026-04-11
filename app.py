import streamlit as st
import anthropic
import os
import json
from datetime import datetime

st.set_page_config(page_title="OPT 273 Contact Lens Simulator", layout="centered")

PATIENTS = {
    "Sarah Chen — 28 y/o, first-time wearer": {
        "initials": "SC",
        "greeting": "Hi! I have an appointment — I'm interested in trying contact lenses for the first time.",
        "profile": """You are Sarah Chen, a 28-year-old graphic designer seeking contact lenses for the first time. Glasses Rx: -3.50 -0.75 x 180 OD, -4.00 -0.75 x 175 OS. You spend 10+ hours/day on screens; eyes feel dry and tired by late evening. No significant medical or ocular history. Wore glasses since age 12. You want contacts for convenience and weekend hiking. No known allergies. Answer as a real patient — conversational, slightly nervous, don't volunteer all information at once. 1–3 sentences per response."""
    },
    "Marcus Webb — 42 y/o, presbyope": {
        "initials": "MW",
        "greeting": "Hi, I have an appointment. I've been wearing contacts for years but I'm having some issues lately.",
        "profile": """You are Marcus Webb, a 42-year-old accountant who wore monthly soft lenses for years but now struggles with near vision and midday dryness. Distance Rx: -2.00 OU, Add: +1.75. Mild dry eye; use Systane Ultra occasionally. Had a red eye from extended wear once — cautious about overnight use. Take lisinopril and loratadine. Interested in multifocal options. Don't over-share; wait for questions. 1–3 sentences per response."""
    },
    "Jordan Lee — 19 y/o, athlete": {
        "initials": "JL",
        "greeting": "Hi, I want to try contact lenses again — I play soccer and my glasses are a problem.",
        "profile": """You are Jordan Lee, a 19-year-old college student and competitive soccer player. Rx: -2.50 -1.75 x 180 OD, -3.00 -2.00 x 175 OS. Tried soft lenses before — felt blurry and kept rotating. Want contacts for sports. Healthy, no medications. Budget is a concern; you'll bring it up if nobody asks. Prefer dailies. Be slightly impatient. 1–3 sentences per response."""
    },
    "Linda Osei — 35 y/o, previous dropout": {
        "initials": "LO",
        "greeting": "Hi, I used to wear contacts but had to stop. I'm wondering if there's something better available now.",
        "profile": """You are Linda Osei, a 35-year-old RN who stopped wearing contact lenses 2 years ago due to dryness and irritation during 12-hour hospital shifts. Wore biweekly soft lenses for 8 years. Told your tear film was borderline. Rx: -1.75 -0.50 x 90 OD, -2.25 -0.75 x 85 OS. A colleague told you about newer daily SiHy lenses; willing to try again but skeptical. No systemic conditions. Be guarded. 1–3 sentences per response."""
    }
}

GRADED_PATIENT = {
    "name": "Derek Kim",
    "initials": "DK",
    "greeting": "Hi, I have an appointment — I'm hoping to talk about getting contact lenses.",
    "profile": """You are Derek Kim, a 31-year-old IT project manager. You wore Acuvue Moist 1-Day lenses for 3 years in your mid-20s but stopped because reordering was inconvenient. You recently started recreational volleyball and your glasses keep slipping. Personal info: DOB August 22, 1993. You have seasonal rhinitis managed with fluticasone nasal spray. You had LASIK consultations twice but were told your corneas were too thin — this makes you slightly anxious. Rx: -4.25 -0.50 x 170 OD, -3.75 sphere OS. You wore dailies, no solution needed, about 10-12 hours/day. Stopped due to inconvenience not discomfort. Don't volunteer medical info unless specifically asked. 1–3 sentences per response."""
}

QUICK_PROMPTS = [
    "What brings you in today?",
    "Have you worn contact lenses before?",
    "Tell me about your glasses prescription.",
    "Do you have any eye conditions or surgeries?",
    "Any medical conditions or medications?",
    "Do you have any allergies?",
    "How many hours a day are you hoping to wear lenses?",
    "What activities would contacts help with?",
    "What is your date of birth?",
    "What do you do for work?",
]

COMPETENCY_ITEMS = [
    "2a — Recorded personal history (name, date of birth, occupation, etc.)",
    "2b — Investigated reasons for seeking contact lenses",
    "2c — Recorded medical health history (diabetes, allergies, arthritis, pregnancy, etc.)",
    "2c — Recorded visual health history",
    "2d — Recorded prior contact lens type and brand",
    "2d — Recorded prior wear time",
    "2d — Recorded prior lens care solutions used"
]

def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=api_key)

def get_ai_response(system_prompt, messages):
    client = get_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text

def get_feedback(messages):
    client = get_client()
    transcript = "\n".join([f"{'Student' if m['role'] == 'user' else 'Patient'}: {m['content']}" for m in messages])
    prompt = f"""You are an optometry clinical instructor evaluating a student's simulated patient interview.

Competency items: {COMPETENCY_ITEMS}

Transcript:
{transcript}

Respond ONLY with valid JSON, no markdown:
{{
  "score": <0-100>,
  "covered": [<items covered>],
  "missed": [<items missed>],
  "praise": "<1-2 sentences>",
  "improvement": "<1-2 sentences>",
  "tip": "<one specific tip>"
}}"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

def send_message(msg, session_key, system_prompt):
    st.session_state[session_key].append({"role": "user", "content": msg})
    reply = get_ai_response(system_prompt, st.session_state[session_key])
    st.session_state[session_key].append({"role": "assistant", "content": reply})
    if session_key == "practice_messages":
        st.session_state.practice_feedback = None
    st.rerun()

# ── UI ──
st.title("OPT 273 — Contact Lens Fitting Simulator")
mode = st.radio("Select mode", ["Practice", "Graded Assignment"], horizontal=True)

# ══════════════════════════════════════════════
# PRACTICE MODE
# ══════════════════════════════════════════════
if mode == "Practice":
    st.markdown("---")
    patient_name = st.selectbox("Choose a patient", list(PATIENTS.keys()))
    patient = PATIENTS[patient_name]

    if "practice_messages" not in st.session_state or st.session_state.get("practice_patient") != patient_name:
        st.session_state.practice_messages = [{"role": "assistant", "content": patient["greeting"]}]
        st.session_state.practice_patient = patient_name
        st.session_state.practice_feedback = None
        st.session_state.practice_input = ""

    # Chat history
    for msg in st.session_state.practice_messages:
        with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
            st.write(msg["content"])

    # Quick prompts
    st.markdown("**Quick prompts**")
    cols = st.columns(2)
    for i, prompt_text in enumerate(QUICK_PROMPTS):
        if cols[i % 2].button(prompt_text, key=f"qp_{i}"):
            send_message(prompt_text, "practice_messages", patient["profile"])

    # Free text input
    st.markdown("")
    if user_input := st.chat_input("Or type your own question…"):
        send_message(user_input, "practice_messages", patient["profile"])

    # Action buttons
    st.markdown("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start over", use_container_width=True):
            st.session_state.practice_messages = [{"role": "assistant", "content": patient["greeting"]}]
            st.session_state.practice_feedback = None
            st.rerun()
    with col2:
        if st.button("Review my interview →", use_container_width=True, type="primary"):
            user_msgs = [m for m in st.session_state.practice_messages if m["role"] == "user"]
            if len(user_msgs) < 3:
                st.warning("Ask a few more questions first.")
            else:
                with st.spinner("Analyzing your interview…"):
                    st.session_state.practice_feedback = get_feedback(st.session_state.practice_messages)

    # Feedback
    if st.session_state.get("practice_feedback"):
        fb = st.session_state.practice_feedback
        st.markdown("---")
        st.subheader("Interview review")
        total = len(fb["covered"]) + len(fb["missed"])
        pct = round(len(fb["covered"]) / total * 100) if total > 0 else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{fb['score']}/100")
        col2.metric("Items covered", f"{len(fb['covered'])}/{total}")
        col3.metric("Competency", f"{pct}%")

        st.markdown("**Competency checklist (2a–2d)**")
        for item in fb["covered"]:
            st.success(f"✓ {item}")
        for item in fb["missed"]:
            st.error(f"✗ {item}")

        st.markdown(f"**What you did well:** {fb['praise']}")
        st.markdown(f"**Areas to improve:** {fb['improvement']}")
        st.markdown(f"**Tip for next time:** {fb['tip']}")
        st.info("You can keep practicing and request feedback again at any time.")

# ══════════════════════════════════════════════
# GRADED MODE
# ══════════════════════════════════════════════
else:
    st.markdown("---")

    if "graded_started" not in st.session_state:
        st.session_state.graded_started = False
        st.session_state.graded_submitted = False
        st.session_state.graded_messages = []
        st.session_state.graded_name = ""
        st.session_state.graded_feedback = None

    if not st.session_state.graded_started:
        st.markdown("### Graded Assignment")
        st.markdown("You will conduct a complete patient interview with a new patient. At the end you will receive feedback and a submission record to upload to Canvas.")
        st.markdown("""
- No prompt suggestions — questions are up to you
- Feedback and submission record generated at the end
- Screenshot or copy your record to submit in Canvas
        """)
        name = st.text_input("Your name (for submission record)")
        if st.button("Begin exam →", type="primary"):
            if name:
                st.session_state.graded_name = name
                st.session_state.graded_started = True
                st.session_state.graded_messages = [{"role": "assistant", "content": GRADED_PATIENT["greeting"]}]
                st.rerun()
            else:
                st.warning("Please enter your name first.")

    elif not st.session_state.graded_submitted:
        st.markdown(f"**Patient:** {GRADED_PATIENT['name']} · **Student:** {st.session_state.graded_name}")

        for msg in st.session_state.graded_messages:
            with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
                st.write(msg["content"])

        if user_input := st.chat_input("Type your question…"):
            send_message(user_input, "graded_messages", GRADED_PATIENT["profile"])

        user_msgs = [m for m in st.session_state.graded_messages if m["role"] == "user"]
        st.caption(f"{len(user_msgs)} exchanges")

        if st.button("Submit & get feedback →", type="primary"):
            if len(user_msgs) < 3:
                st.warning("Please conduct your interview before submitting.")
            else:
                st.session_state.graded_submitted = True
                st.rerun()

    else:
        st.markdown("### Submission record")
        st.success("Interview submitted successfully.")

        if not st.session_state.graded_feedback:
            with st.spinner("Generating feedback…"):
                st.session_state.graded_feedback = get_feedback(st.session_state.graded_messages)

        fb = st.session_state.graded_feedback
        now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        user_msgs = [m for m in st.session_state.graded_messages if m["role"] == "user"]

        col1, col2 = st.columns(2)
        col1.markdown(f"**Student:** {st.session_state.graded_name}")
        col1.markdown(f"**Patient:** {GRADED_PATIENT['name']}")
        col2.markdown(f"**Date:** {now}")
        col2.markdown(f"**Exchanges:** {len(user_msgs)}")

        st.markdown("---")
        total = len(fb["covered"]) + len(fb["missed"])
        pct = round(len(fb["covered"]) / total * 100) if total > 0 else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Score", f"{fb['score']}/100")
        col2.metric("Items covered", f"{len(fb['covered'])}/{total}")
        col3.metric("Competency", f"{pct}%")

        st.markdown("**Competency checklist (2a–2d)**")
        for item in fb["covered"]:
            st.success(f"✓ {item}")
        for item in fb["missed"]:
            st.error(f"✗ {item}")

        st.markdown(f"**What you did well:** {fb['praise']}")
        st.markdown(f"**Areas to improve:** {fb['improvement']}")
        st.markdown(f"**Tip for next time:** {fb['tip']}")

        st.markdown("---")
        st.markdown("**Interview transcript**")
        transcript = "\n\n".join([f"{'STUDENT' if m['role'] == 'user' else 'PATIENT'}: {m['content']}" for m in st.session_state.graded_messages])
        st.text_area("Copy this to submit to your instructor", transcript, height=300)
        st.caption("Screenshot this page or copy the transcript to paste into your Canvas submission.")
