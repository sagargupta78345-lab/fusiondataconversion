import streamlit as st
import anthropic
import os
from knowledge_base import (
    build_knowledge_base,
    search_modules,
    format_context,
    get_all_module_titles,
)

st.set_page_config(
    page_title="Fusion Data Conversion Agent",
    page_icon="🔄",
    layout="wide",
)

SYSTEM_PROMPT = """You are an expert Oracle Fusion Data Conversion AI assistant with deep knowledge of:

- Oracle Fusion Cloud ERP data migration strategies
- FBDI (File Based Data Import) — for millions of records
- File Based Loader (FBL) / Import Management — for thousands of records
- ADFdi Spreadsheet Loader — for hundreds to thousands of records
- SOAP Web Services for Oracle Fusion (ERP Integration Service, ExternalReportWSSService, PurchaseOrderService)
- REST APIs for Oracle Fusion (importBulkData, importActivities, AR Invoice, Receipts)
- PL/SQL development for Fusion integration (APEX_WEB_SERVICE, DBMS_SCHEDULER, DBMS_SQL)
- Oracle ATP (Autonomous Transaction Processing) Database
- BI Publisher Report Service and Scheduler Service for data extraction
- End-to-end data migration automation frameworks

You have access to a structured knowledge base from a 21-module Fusion Data Conversion course covering real-world PL/SQL packages, SQL scripts, SOAP payloads, and REST API examples.

Guidelines:
- Answer questions clearly and accurately based on the provided context
- When generating PL/SQL or SQL code, follow the patterns from the knowledge base
- For step-by-step guidance, break down the process clearly with numbered steps
- When explaining code, reference the actual package/procedure names from the repo
- If a question is outside the knowledge base scope, say so clearly
- Always mention which module covers a topic when relevant
"""


@st.cache_resource(show_spinner="Loading Fusion knowledge base...")
def load_kb():
    return build_knowledge_base()


def get_claude_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def chat_with_agent(client: anthropic.Anthropic, messages: list, context: str) -> str:
    system = SYSTEM_PROMPT
    if context:
        system += f"\n\n--- RELEVANT KNOWLEDGE BASE CONTEXT ---\n{context}"

    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    return response.content[0].text


# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🔄 Fusion Agent")
    st.markdown("**Oracle Fusion Data Conversion AI**")
    st.divider()

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        placeholder="sk-ant-...",
        help="Get your key from console.anthropic.com",
    )

    st.divider()
    st.markdown("### 📚 Knowledge Base")
    st.caption("21 modules loaded from your GitHub repo")

    kb = load_kb()
    module_titles = get_all_module_titles(kb)

    with st.expander("View all modules", expanded=False):
        for num, title in module_titles:
            st.markdown(f"**{num}.** {title}")

    st.divider()
    st.markdown("### 💡 Try asking:")
    example_questions = [
        "What is FBDI and when should I use it?",
        "How does DBMS_SCHEDULER work for sync jobs?",
        "Show me PL/SQL code to call importBulkData SOAP service",
        "Explain the difference between Report Service and Scheduler Service",
        "How to invoke a REST API from Oracle Database?",
        "Walk me through the E2E data migration automation process",
        "How to pre-validate GL Journal data before import?",
    ]
    for q in example_questions:
        if st.button(q, use_container_width=True, key=q):
            st.session_state.pending_question = q

    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Main Chat ─────────────────────────────────────────────────────────────────

st.title("🔄 Oracle Fusion Data Conversion Agent")
st.caption("Ask me anything about Oracle Fusion data migration, PL/SQL, SOAP/REST APIs, FBDI, DBMS_SCHEDULER, and more.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle example question click
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None
else:
    user_input = st.chat_input("Ask about Fusion data conversion...")

if user_input:
    if not api_key:
        st.error("Please enter your Anthropic API key in the sidebar.")
        st.stop()

    # Show user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Retrieve relevant context
    relevant_modules = search_modules(kb, user_input, top_k=3)
    context = format_context(kb, relevant_modules)

    # Show which modules are being used (subtle)
    if relevant_modules:
        module_refs = ", ".join(
            [f"Module {n}" for n in relevant_modules if n in kb]
        )
        st.caption(f"Referencing: {module_refs}")

    # Get Claude response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                client = get_claude_client(api_key)
                # Build messages for API (exclude system, already in SYSTEM_PROMPT)
                api_messages = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
                response = chat_with_agent(client, api_messages, context)
                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
            except anthropic.AuthenticationError:
                st.error("Invalid API key. Please check your Anthropic API key.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
