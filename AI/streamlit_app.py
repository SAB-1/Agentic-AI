# -*- coding: utf-8 -*-
"""
AI Twin Chat App — Streamlit version (Genie-style light UI)
Converted from chatbot.ipynb (Colab) into a deployable Streamlit app.

CORE LOGIC UNCHANGED from the original notebook:
- PDF/summary loading
- system_prompt construction
- OpenAI client setup (OpenRouter base_url, API_TOKEN env var)
- the chat-completion call itself (model, messages shape, stream=False)

ADDED on top, without touching the above:
- A light, lavender, card-based UI styled after the referenced Genie
  Chatbot design (soft white panels, pill input, rounded action chips).
- A real "Chat Files" upload feature: an uploaded PDF/TXT/image's content
  is extracted and folded into that turn's context as extra information,
  the same way the original profile.pdf is folded in — it does not replace
  or modify the original system_prompt logic.
"""

from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
import streamlit as st
from pydantic import BaseModel
import os
import io

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Ayomide's AI Twin",
    page_icon="✨",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Load profile PDF (unchanged logic) — cached so it only runs once per session
# ---------------------------------------------------------------------------
@st.cache_resource
def load_profile_summary():
    pdfReader = PdfReader("Resources/profile.pdf")
    prof_summary = ""
    for page in pdfReader.pages:
        text = page.extract_text()
        if text:
            prof_summary += text + "\n"
    return prof_summary


@st.cache_resource
def load_summary():
    with open("Resources/Summary.txt", "r", encoding="utf-8") as file:
        return file.read()


prof_summary = load_profile_summary()
summary = load_summary()

# ---------------------------------------------------------------------------
# Load API key (unchanged logic)
# ---------------------------------------------------------------------------
load_dotenv(override=True)
openai_api_key = os.getenv("API_TOKEN")
if openai_api_key:
    print(f"OpenAI API Key exists and begins with {openai_api_key[:14]}")
else:
    print(f"OpenAI API Key not set - please check")

# ---------------------------------------------------------------------------
# System prompt (unchanged logic)
# ---------------------------------------------------------------------------
name = "Sowande, Ayomide Boluwatife"
system_prompt = (
    f"You are acting as {name}, representing {name} on their website. "
    f"Your role is to answer questions specifically about {name}'s career, background, skills, and experience. "
    f"You must faithfully and accurately portray {name} in all interactions. "
    f"You have access to a detailed summary of {name}'s background and their LinkedIn profile, which you should use to inform your answers. "
    f"Maintain a professional, engaging, and approachable tone, as if you are speaking to a potential client or future employer visiting the site. "
    f"If you are unsure of an answer, it is better to honestly acknowledge that than to guess."
    f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{prof_summary}\n\n"
    f"Using this context, please converse naturally and consistently, always staying in character as {name}."
)

# ---------------------------------------------------------------------------
# OpenAI client (unchanged logic) — cached so it's created once
# ---------------------------------------------------------------------------
@st.cache_resource
def get_client():
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openai_api_key
    )
    print("OpenAI Client created", client)
    return client


openai_python_client = get_client()


# ---------------------------------------------------------------------------
# Chat function — same call as the original `livechat`
# ---------------------------------------------------------------------------
def livechat(message, history):
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai_python_client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=messages,
        stream=False
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# File upload helper — extracts text from an uploaded file so it can be
# folded into the conversation as extra context. New feature, additive only.
# ---------------------------------------------------------------------------
def extract_uploaded_file_text(uploaded_file):
    name_lower = uploaded_file.name.lower()
    try:
        if name_lower.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        elif name_lower.endswith(".txt"):
            return uploaded_file.getvalue().decode("utf-8", errors="ignore").strip()
        else:
            return None  # images etc. are attached visually but not text-extracted
    except Exception as e:
        return f"[Could not read file: {e}]"


def file_icon_for(filename):
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "📕", "#FDE2E2"
    if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return "🖼️", "#E1ECFD"
    if lower.endswith(".txt"):
        return "📄", "#E6F4EA"
    return "📎", "#EDE7FB"


# ---------------------------------------------------------------------------
# UI — Genie-inspired LIGHT lavender chat interface
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg-wash-1: #f3eefb;
    --bg-wash-2: #fbf8fd;
    --panel-white: #ffffff;
    --border-soft: rgba(20, 10, 40, 0.06);
    --text-primary: #1a1a22;
    --text-secondary: #8d8a9b;
    --text-faint: #b4b1c2;
    --ink-button: #1c1c24;
    --chip-blue: #e1ecfd;
    --chip-blue-icon: #4a86f7;
    --chip-pink: #fde2ea;
    --chip-pink-icon: #ef5d8c;
    --chip-green: #e3f6ea;
    --chip-green-icon: #34b266;
    --chip-violet: #ede7fb;
    --chip-violet-icon: #8a5cf6;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: radial-gradient(circle at 10% 0%, var(--bg-wash-1), transparent 55%),
                radial-gradient(circle at 90% 10%, #eef3fd, transparent 50%),
                var(--bg-wash-2) !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stHeader"] { background: transparent !important; }

.block-container {
    max-width: 720px;
    padding-top: 1.6rem;
    padding-bottom: 2rem;
}

/* ---------- Greeting header ---------- */
#greeting-row {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 22px;
}
.avatar-circle {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--chip-violet-icon), var(--chip-pink-icon));
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}
.greeting-text p.line1 {
    font-size: 14px;
    color: var(--text-secondary);
    margin: 0;
    font-weight: 500;
}
.greeting-text p.line2 {
    font-size: 21px;
    color: var(--text-primary);
    margin: 2px 0 0 0;
    font-weight: 700;
    letter-spacing: -0.01em;
    line-height: 1.3;
}

/* ---------- Chat messages ---------- */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 6px 0 !important;
}
[data-testid="stChatMessageContent"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    color: var(--text-primary) !important;
}

/* Assistant message = plain white answer card, no heavy bubble chrome */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageContent"] {
    background: var(--panel-white) !important;
    border: 1px solid var(--border-soft) !important;
    border-radius: 18px !important;
    padding: 16px 18px !important;
    box-shadow: 0 8px 24px rgba(80, 60, 140, 0.06);
}

/* User message = soft violet tint, right-leaning */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
    background: var(--chip-violet) !important;
    border-radius: 18px !important;
    padding: 14px 18px !important;
    color: var(--text-primary) !important;
}

/* Hide default avatar icons for a cleaner card-only look */
[data-testid="chatAvatarIcon-user"], [data-testid="chatAvatarIcon-assistant"] {
    display: none !important;
}

/* ---------- File chip row (uploaded files) ---------- */
.file-chip-row {
    display: flex;
    gap: 10px;
    margin: 10px 0 4px 0;
    flex-wrap: wrap;
}
.file-chip {
    background: var(--panel-white);
    border: 1px solid var(--border-soft);
    border-radius: 14px;
    padding: 8px 14px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
    color: var(--text-secondary);
    box-shadow: 0 6px 16px rgba(80, 60, 140, 0.06);
}
.file-chip .icon-box {
    width: 26px;
    height: 26px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
}
.file-chip .file-name {
    color: var(--text-primary);
    font-weight: 600;
}

/* ---------- Action chips row ---------- */
.action-chip-label {
    font-size: 12px;
    color: var(--text-secondary);
    text-align: center;
    margin-top: 6px;
    font-weight: 500;
}

div[data-testid="column"] button {
    background: var(--panel-white) !important;
    border: 1px solid var(--border-soft) !important;
    border-radius: 16px !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    box-shadow: 0 6px 16px rgba(80, 60, 140, 0.05);
    transition: transform 0.15s ease;
}
div[data-testid="column"] button:hover {
    transform: translateY(-2px);
    border-color: var(--chip-violet-icon) !important;
}

/* ---------- Chat input ---------- */
[data-testid="stChatInput"] {
    background: transparent !important;
}
[data-testid="stChatInput"] textarea {
    background: var(--panel-white) !important;
    border: 1px solid var(--border-soft) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    border-radius: 24px !important;
    box-shadow: 0 8px 24px rgba(80, 60, 140, 0.07);
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--chip-violet-icon) !important;
    box-shadow: 0 0 0 2px rgba(138, 92, 246, 0.18) !important;
}
[data-testid="stChatInput"] button {
    background: var(--ink-button) !important;
    border-radius: 50% !important;
}

/* File uploader styling to match light theme */
[data-testid="stFileUploader"] {
    background: var(--panel-white);
    border: 1px dashed var(--border-soft);
    border-radius: 16px;
    padding: 10px;
}
[data-testid="stFileUploader"] section {
    background: transparent !important;
}

#footer-note {
    text-align: center;
    color: var(--text-faint);
    font-size: 11.5px;
    margin-top: 20px;
}

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-thumb { background: rgba(138, 92, 246, 0.25); border-radius: 8px; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div id="greeting-row">
        <div class="avatar-circle">✨</div>
        <div class="greeting-text">
            <p class="line1">Hi 👋</p>
            <p class="line2">I'm Ayomide's Digital Twin... Ask me anything about him professionally.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_uploader" not in st.session_state:
    st.session_state.show_uploader = False
if "pending_file_context" not in st.session_state:
    st.session_state.pending_file_context = None
if "pending_file_name" not in st.session_state:
    st.session_state.pending_file_name = None

# ---------------------------------------------------------------------------
# Starter examples (only before first message)
# ---------------------------------------------------------------------------
example_clicked = None
if len(st.session_state.messages) == 0:
    ex_cols = st.columns(3)
    examples = [
        "What's your professional background?",
        "What are you most skilled at?",
        "Tell me about a project you're proud of.",
    ]
    for col, example in zip(ex_cols, examples):
        if col.button(example, use_container_width=True, key=f"ex_{example}"):
            example_clicked = example

# ---------------------------------------------------------------------------
# Render chat history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Action chips row (Chat Files / Images / Translate / Audio Chat)
# "Chat Files" is wired to a real file uploader; the others are presented
# in the same visual style but are not separate live features yet.
# ---------------------------------------------------------------------------
chip_cols = st.columns(4)
chip_defs = [
    ("📁", "Chat Files", "chip_files"),
    ("🖼️", "Images", "chip_images"),
    ("🌐", "Translate", "chip_translate"),
    ("🎙️", "Audio Chat", "chip_audio"),
]
for col, (icon, label, key) in zip(chip_cols, chip_defs):
    with col:
        clicked = st.button(f"{icon}\n{label}", use_container_width=True, key=key)
        if key == "chip_files" and clicked:
            st.session_state.show_uploader = not st.session_state.show_uploader

if st.session_state.show_uploader:
    uploaded_file = st.file_uploader(
        "Upload a file to chat about",
        type=["pdf", "txt", "png", "jpg", "jpeg"],
        key="file_uploader",
        label_visibility="collapsed",
    )
    if uploaded_file is not None:
        extracted = extract_uploaded_file_text(uploaded_file)
        st.session_state.pending_file_context = extracted
        st.session_state.pending_file_name = uploaded_file.name

        icon, bg = file_icon_for(uploaded_file.name)
        st.markdown(
            f"""
            <div class="file-chip-row">
                <div class="file-chip">
                    <div class="icon-box" style="background:{bg};">{icon}</div>
                    <span class="file-name">{uploaded_file.name}</span>
                    <span>attached &mdash; ask a question about it below</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask me anything ...")
final_input = user_input or example_clicked

if final_input:
    # If a file was uploaded this turn, fold its extracted text in as extra
    # context for just this message — additive on top of the original logic,
    # not a change to system_prompt or the original livechat() call shape.
    message_for_model = final_input
    if st.session_state.pending_file_context:
        message_for_model = (
            f"{final_input}\n\n"
            f"[Attached file: {st.session_state.pending_file_name}]\n"
            f"{st.session_state.pending_file_context}"
        )

    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.chat_message("user"):
        st.markdown(final_input)

    history_for_call = st.session_state.messages[:-1]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = livechat(message_for_model, history_for_call)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Clear the pending file after it's been used once
    st.session_state.pending_file_context = None
    st.session_state.pending_file_name = None
    st.session_state.show_uploader = False
    st.rerun()

st.markdown(
    '<div id="footer-note">Responses are generated by an AI standing in for Ayomide &mdash; not Ayomide directly.</div>',
    unsafe_allow_html=True,
)