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
        
        # Product Table / Cards View
        products = result["retrieved_products"]
        st.markdown(f"#### Retrieved Documents ({len(products)} records found)")

        if products:
            cols = st.columns(3)
            for i, p in enumerate(products):
                m = p["metadata"]
                dist = p.get("distance")
                stock = m.get("statut_stock", "Unknown")
                
                # Dynamic technical clean status strings (No emojis)
                if "Disponible" in stock:
                    stock_status = "Available"
                elif "commande" in stock.lower():
                    stock_status = "On Order"
                else:
                    stock_status = "Out of Stock"
                
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"##### {m.get('nom', 'N/A')}")
                        st.markdown(f"**Category:** {m.get('categorie', 'N/A')}")
                        st.markdown(f"**Price:** {m.get('prix', 'N/A')} DA")
                        
                        col_card_l, col_card_r = st.columns(2)
                        with col_card_l:
                            st.caption(f"Status: {stock_status}")
                        with col_card_r:
                            st.caption(f"Distance: {f'{dist:.4f}' if dist is not None else 'N/A'}")
        else:
            st.warning("No candidate records returned by the vector similarity search engine.")

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

# --- TECHNICAL METRICS SIDEBAR ---
with st.sidebar:
    st.subheader("Session Pipeline Data")
    st.markdown(f"**Active Session Length:** {st.session_state.chat.turns.get_turn_count()} Turns Processed")
    st.markdown("---")
    
    st.markdown("**Dialogue Log Grid:**")
    for msg in st.session_state.chat.history.get_history():
        role_tag = "USER" if msg["role"] == "user" else "ASSISTANT"
        st.text_area(
            label=f"[{role_tag}]", 
            value=msg['content'], 
            height=68, 
            disabled=True,
            key=f"sidebar_msg_{msg['content'][:10]}_{result['turn_count']}" if 'result' in locals() else None
        )

    st.markdown("---")
    if st.button("Reset Global Pipeline Cache", use_container_width=True, type="primary"):
        del st.session_state["chat"]
        del st.session_state["results"]
        st.rerun()