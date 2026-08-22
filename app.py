import streamlit as st
import anthropic
import os
import json
from datetime import datetime

st.set_page_config(page_title="Subjective Interview Simulator", layout="centered")

PATIENTS = {
    "Sarah Chen — 28 y/o, first-time wearer": {
        "initials": "SC",
        "greeting": "Hi! I have an appointment — I'm interested in trying contact lenses for the first time.",
        "profile": """You are Sarah Chen, a 28-year-old graphic designer seeking contact lenses for the first time. Glasses Rx: -3.50 -0.75 x 180 OD, -4.00 -0.75 x 175 OS. You spend 10+ hours/day on screens; eyes feel dry and tired by late evening. No significant medical or ocular history. Wore glasses since age 12. You want contacts for convenience and weekend hiking. No known allergies. Answer as a real patient — conversational, slightly nervous, don't volunteer all information at once. Wait for the student to ask appropriate follow-up questions before sharing details. 1–3 sentences per response."""
    },
    "Marcus Webb — 42 y/o, presbyope": {
        "initials": "MW",
        "greeting": "Hi, I have an appointment. I've been wearing contacts for years but I'm having some issues lately.",
        "profile": """You are Marcus Webb, a 42-year-old accountant who wore monthly soft lenses for years but now struggles with near vision and midday dryness. Distance Rx: -2.00 OU, Add: +1.75. Mild dry eye; use Systane Ultra occasionally. Had a red eye from extended wear once — cautious about overnight use. Take lisinopril and loratadine. Interested in multifocal options. Don't over-share; wait for the student to ask appropriate questions before sharing details. 1–3 sentences per response."""
    },
    "Jordan Lee — 19 y/o, athlete": {
        "initials": "JL",
        "greeting": "Hi, I want to try contact lenses again — I play soccer and my glasses are a problem.",
        "profile": """You are Jordan Lee, a 19-year-old college student and competitive soccer player. Rx: -2.50 -1.75 x 180 OD, -3.00 -2.00 x 175 OS. Tried soft lenses before — felt blurry and kept rotating. Want contacts for sports. Healthy, no medications. Budget is a concern; you'll bring it up if directly asked about preferences or cost. Prefer dailies. Be slightly impatient. Don't volunteer all details at once — wait for appropriate follow-up questions. 1–3 sentences per response."""
    },
    "Linda Osei — 35 y/o, previous dropout": {
        "initials": "LO",
        "greeting": "Hi, I used to wear contacts but had to stop. I'm wondering if there's something better available now.",
        "profile": """You are Linda Osei, a 35-year-old RN who stopped wearing contact lenses 2 years ago due to dryness and irritation during 12-hour hospital shifts. Wore biweekly soft lenses for 8 years. Told your tear film was borderline. Rx: -1.75 -0.50 x 90 OD, -2.25 -0.75 x 85 OS. A colleague told you about newer daily SiHy lenses; willing to try again but skeptical. No systemic conditions. Be guarded and wait for the student to ask before sharing details. 1–3 sentences per response."""
    },
    "Derek Kim — 31 y/o, previous daily lens wearer": {
        "initials": "DK",
        "greeting": "Hi, I have an appointment — I'm hoping to talk about getting contact lenses.",
        "profile": """You are Derek Kim, a 31-year-old IT project manager. You wore Acuvue Moist 1-Day lenses for 3 years in your mid-20s but stopped because reordering was inconvenient. You recently started recreational volleyball and your glasses keep slipping. Personal info: DOB August 22, 1993. Always answer demographic questions directly and cooperatively when asked — name, date of birth, occupation, phone, and address. You have seasonal rhinitis managed with fluticasone nasal spray. You had LASIK consultations twice but were told your corneas were too thin — this makes you slightly anxious. Rx: -4.25 -0.50 x 170 OD, -3.75 sphere OS. You wore dailies, no solution needed, about 10-12 hours/day. Stopped due to inconvenience not discomfort. Always answer demographic questions directly and cooperatively when asked. Don't volunteer medical info unless specifically asked. 1–3 sentences per response."""
    }
}

COMPETENCY_ITEMS = [
    "2a — Personal history (name, date of birth, occupation)",
    "2b — Reasons for seeking contact lenses",
    "2c — Medical health history (systemic conditions, allergies, medications)",
    "2c — Visual/ocular health history",
    "2d — Prior contact lens type and brand",
    "2d — Prior wear time",
    "2d — Prior lens care solutions used"
]

QUICK_PROMPTS = [
    "What brings you in today?",
    "Have you worn contact lenses before?",
    "Do you have any medical conditions or allergies?",
    "Are you currently taking any medications?",
    "Can you tell me about your eye health history?",
    "What is your date of birth?",
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

def get_feedback(messages, patient_name):
    client = get_client()
    transcript = "\n".join([f"{'Student' if m['role'] == 'user' else 'Patient'}: {m['content']}" for m in messages])
    prompt = f"""You are an experienced optometry clinical instructor reviewing a student's patient interview practice session. The patient was {patient_name}.

The following are the key areas a thorough subjective interview should cover:
{json.dumps(COMPETENCY_ITEMS, indent=2)}

Transcript:
{transcript}

Provide formative coaching feedback — not a score, grade, or pass/fail evaluation. Your feedback should help the student grow as a clinical interviewer.

Respond ONLY with valid JSON, no markdown or code blocks:
{{
  "explored_well": "<2-3 sentences identifying what the student did effectively in the interview>",
  "missed_or_thin": "<2-3 sentences identifying important areas that were missed entirely or not explored thoroughly enough>",
  "follow_up_suggestions": "<2-3 specific follow-up questions or interviewing considerations the student should keep in mind for next time>"
}}"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)

def send_message(msg):
    patient = PATIENTS[st.session_state.selected_patient]
    st.session_state.messages.append({"role": "user", "content": msg})
    reply = get_ai_response(patient["profile"], st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.feedback = None
    st.rerun()

def reset_session(patient_name=None):
    if patient_name:
        st.session_state.selected_patient = patient_name
    patient = PATIENTS[st.session_state.selected_patient]
    st.session_state.messages = [{"role": "assistant", "content": patient["greeting"]}]
    st.session_state.feedback = None
    st.session_state.interview_ended = False

# ── Session state init ──
if "selected_patient" not in st.session_state:
    st.session_state.selected_patient = list(PATIENTS.keys())[0]
    st.session_state.messages = []
    st.session_state.feedback = None
    st.session_state.interview_ended = False
    reset_session()

# ── UI ──
st.title("Subjective Interview Simulator")
st.markdown("Approach this simulation as you would a real patient interview. Respond to what the patient tells you and use follow-up questions when appropriate. Practice using open-ended questions to encourage the patient to share information in their own words. There is no required script or checklist — focus on having a natural clinical conversation.")
st.markdown("---")

# ── Patient selector ──
st.markdown("**Select a patient**")
patient_name = st.selectbox("", list(PATIENTS.keys()), index=list(PATIENTS.keys()).index(st.session_state.selected_patient), label_visibility="collapsed")

if patient_name != st.session_state.selected_patient:
    reset_session(patient_name)
    st.rerun()

st.markdown("---")

# ── Chat ──
for msg in st.session_state.messages:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.write(msg["content"])

# ── Input and prompts ──
if not st.session_state.interview_ended:
    st.markdown("**Quick prompts**")
    cols = st.columns(2)
    for i, prompt_text in enumerate(QUICK_PROMPTS):
        if cols[i % 2].button(prompt_text, key=f"qp_{i}"):
            send_message(prompt_text)

    st.markdown("")
    if user_input := st.chat_input("Or type your own question…"):
        send_message(user_input)

    st.markdown("")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start over", use_container_width=True):
            reset_session()
            st.rerun()
    with col2:
        if st.button("End interview & review feedback →", use_container_width=True, type="primary"):
            user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
            if len(user_msgs) < 3:
                st.warning("Continue your interview a little longer before reviewing feedback.")
            else:
                st.session_state.interview_ended = True
                with st.spinner("Reviewing your interview…"):
                    st.session_state.feedback = get_feedback(st.session_state.messages, patient_name)
                st.rerun()

# ── Feedback and transcript ──
if st.session_state.interview_ended and st.session_state.feedback:
    fb = st.session_state.feedback
    st.markdown("---")
    st.subheader("Interview feedback")

    st.markdown("**What you explored effectively**")
    st.success(fb["explored_well"])

    st.markdown("**Areas that were missed or could be explored further**")
    st.warning(fb["missed_or_thin"])

    st.markdown("**Suggestions for follow-up questions and interviewing considerations**")
    st.info(fb["follow_up_suggestions"])

    st.markdown("---")
    st.markdown("**Interview transcript**")
    transcript = "\n\n".join([
        f"{'STUDENT' if m['role'] == 'user' else 'PATIENT'}: {m['content']}"
        for m in st.session_state.messages
    ])
    st.text_area("", transcript, height=300, label_visibility="collapsed")

    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    exchanges = len([m for m in st.session_state.messages if m["role"] == "user"])
    download_text = f"""Subjective Interview Simulator
Patient: {patient_name}
Date: {now}
Exchanges: {exchanges}

INTERVIEW FEEDBACK

What you explored effectively:
{fb['explored_well']}

Areas that were missed or could be explored further:
{fb['missed_or_thin']}

Suggestions for follow-up questions and interviewing considerations:
{fb['follow_up_suggestions']}

TRANSCRIPT
{transcript}"""

    st.download_button(
        "Download transcript & feedback",
        data=download_text,
        file_name="interview-transcript.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.markdown("")
    if st.button("Start another patient encounter →", use_container_width=True):
        reset_session()
        st.rerun()
