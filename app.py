import streamlit as st
from src.chat import ChatManager

# Professional engineering layout configuration
st.set_page_config(
    page_title="Energical — RAG Diagnostic Suite", 
    layout="wide"
)

st.title("Energical RAG Diagnostics Suite")
st.caption("Internal Validation Dashboard — Integration Phase 4A + Phase 3")
st.markdown("---")

# Thread State Management Initialization
if "chat" not in st.session_state:
    with st.spinner("Connecting to localized data clusters and loading vector weights..."):
        st.session_state.chat = ChatManager()

if "results" not in st.session_state:
    st.session_state.results = []

# --- CHAT STARTER TEMPLATES ---
# Displays only when there are no active results to mirror a clean chat onboarding flow
if not st.session_state.results:
    st.markdown("#### Suggested Inquiries")
    st.caption("Select a diagnostic template below to test cross-lingual retrieval performance:")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        if st.button("bghit chaudiere dial gaz", use_container_width=True):
            st.session_state.results.append(st.session_state.chat.send_message("bghit chaudiere dial gaz"))
            st.rerun()
    with col_t2:
        if st.button("Recherche mitigeur lavabo chrome", use_container_width=True):
            st.session_state.results.append(st.session_state.chat.send_message("Recherche mitigeur lavabo chrome"))
            st.rerun()
    with col_t3:
        if st.button("khasni bomba dial lma", use_container_width=True):
            st.session_state.results.append(st.session_state.chat.send_message("khasni bomba dial lma"))
            st.rerun()
    st.markdown("---")

# Main conversational intake
user_input = st.chat_input("Input query (Français, Darija, Arabic)...")

if user_input:
    result = st.session_state.chat.send_message(user_input)
    st.session_state.results.append(result)

# --- RESULTS PROCESSING PIPELINE ---
for result in st.session_state.results:
    with st.container(border=True):
        # Top Metadata Row
        col_meta_left, col_meta_right = st.columns([1, 4])
        with col_meta_left:
            st.markdown(f"**Turn:** {result['turn_count']}")
        with col_meta_right:
            st.markdown(f"**Compiled Search Anchor:** `{result['retrieval_query']}`")
            
        st.markdown(f"**User Utterance:** {result['user_message']}")
        
        # Extracted Context / Slots Information
        mem = result["memory"]
        filled = {k: v for k, v in mem.items() if v is not None}
        if filled:
            memory_string = " | ".join(f"**{k}:** {v}" for k, v in filled.items())
            st.markdown(f"**Extracted Context:** {memory_string}")
        else:
            st.markdown("**Extracted Context:** No state variables extracted from string.")

        st.markdown("---")
        
        

        # Bottom Debug Footer
        dialogue = result.get("dialogue")
        if dialogue:
            score = dialogue.get("score", 0)
            family = dialogue.get("family", "N/A")
            lang = dialogue.get("language", "N/A")
            st.caption(
                f"Classification Metrics — Family: {family} | "
                f"Language Profile: {lang} | Structural Match Score: {score:.3f}"
            )
            
            
            # ── NEW: LLM RECOMMENDATION PANEL ────────────────────
        st.markdown("---")
        st.markdown("#### AI Recommendation")

        status   = result.get("business_status", "")
        allowed  = result.get("allow_recommendation", False)
        llm_answer = result.get("llm_answer", "")
        missing  = result.get("missing_information", [])

        if allowed and llm_answer:
            st.success(llm_answer)

        elif status == "NOT_ENOUGH_TURNS":
            st.info("Still collecting information — minimum 3 turns required before recommendation.")

        elif status == "MISSING_INFORMATION":
            st.warning(
                "Missing required fields: "
                + ", ".join(missing)
            )
            if llm_answer:
                st.info(llm_answer)

        elif status in ("NO_PRODUCTS_FOUND", "NO_AVAILABLE_PRODUCTS"):
            st.error("No available products found for this request.")
            if llm_answer:
                st.info(llm_answer)

        elif status == "UNKNOWN_CATEGORY":
            st.warning("Category not recognized.")

        else:
            if llm_answer:
                st.info(llm_answer)
        # ─────────────────────────────────────────────────────

# --- TECHNICAL METRICS SIDEBAR ---
with st.sidebar:
    st.subheader("Session Pipeline Data")
    st.markdown(
        f"**Active Session Length:** {st.session_state.chat.turns.get_turn_count()} Turns Processed"
    )
    st.markdown("---")

    st.markdown("**Dialogue Log Grid:**")

    history = st.session_state.chat.history.get_history()

    for i, msg in enumerate(history):
        role_tag = "USER" if msg["role"] == "user" else "ASSISTANT"

        st.text_area(
            label=f"[{role_tag}]",
            value=msg["content"],
            height=68,
            disabled=True,
            key=f"sidebar_msg_{i}"
        )

    st.markdown("---")

    if st.button(
        "Reset Global Pipeline Cache",
        key="reset_cache_button",
        use_container_width=True,
        type="primary",
    ):
        del st.session_state["chat"]
        del st.session_state["results"]
        st.rerun()