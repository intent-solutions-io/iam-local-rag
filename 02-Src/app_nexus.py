"""
NEXUS Streamlit UI - Hybrid Cloud RAG Interface
UI shim for NEXUS core pipeline with multi-provider support.
"""
import streamlit as st
import os
import time
from pathlib import Path
from typing import List

# Import NEXUS core components
from nexus.core.rag_pipeline import RAGPipeline
from nexus.core.router import ProviderRouter
from nexus.core.config import Config, NexusMode
from nexus.core.models import QueryRequest, IndexRequest


# --- Page Configuration ---
st.set_page_config(
    page_title="NEXUS - Hybrid Cloud RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- Session State Initialization ---
if "pipeline" not in st.session_state:
    st.session_state.pipeline = None
if "workspace_id" not in st.session_state:
    st.session_state.workspace_id = "default"
if "query_history" not in st.session_state:
    st.session_state.query_history = []


# --- Sidebar Configuration ---
with st.sidebar:
    st.title("⚙️ NEXUS Configuration")

    # Mode selection
    st.subheader("Operating Mode")
    mode = st.selectbox(
        "Select Mode",
        options=[m.value for m in NexusMode],
        index=[m.value for m in NexusMode].index(Config.NEXUS_MODE.value),
        help="LOCAL: Ollama only | CLOUD: Cloud providers | HYBRID: Local retrieval + Cloud LLM"
    )

    # Provider selection
    st.subheader("Providers")

    # LLM Provider
    llm_provider = st.selectbox(
        "LLM Provider",
        options=["ollama", "anthropic", "openai", "vertex"],
        index=["ollama", "anthropic", "openai", "vertex"].index(Config.NEXUS_LLM_PROVIDER.value),
        help="Provider for text generation"
    )

    # Embedding Provider
    embed_provider = st.selectbox(
        "Embedding Provider",
        options=["ollama", "openai", "vertex"],
        index=["ollama", "openai", "vertex"].index(Config.NEXUS_EMBED_PROVIDER.value),
        help="Provider for document embeddings"
    )

    # Workspace
    st.subheader("Workspace")
    workspace_id = st.text_input(
        "Workspace ID",
        value=st.session_state.workspace_id,
        help="Isolate documents by workspace"
    )
    if workspace_id != st.session_state.workspace_id:
        st.session_state.workspace_id = workspace_id
        st.session_state.pipeline = None  # Force recreation

    # Hybrid Safety
    st.subheader("Privacy Settings")
    hybrid_safe = st.checkbox(
        "Hybrid Safe Mode",
        value=Config.HYBRID_SAFE_MODE,
        help="Only send snippets (not full docs) to cloud providers"
    )

    max_snippet_length = st.slider(
        "Max Snippet Length",
        min_value=500,
        max_value=8000,
        value=Config.MAX_SNIPPET_LENGTH,
        step=500,
        help="Maximum characters per snippet sent to cloud"
    )

    # Initialize button
    if st.button("🔧 Initialize Pipeline", type="primary"):
        with st.spinner("Initializing NEXUS pipeline..."):
            try:
                # Validate configuration
                validation = ProviderRouter.validate_configuration()

                if not validation.get("valid", False):
                    st.error("❌ Configuration validation failed")
                    for error in validation.get("errors", []):
                        st.error(f"• {error}")
                    st.stop()

                # Show warnings
                for warning in validation.get("warnings", []):
                    st.warning(f"⚠️ {warning}")

                # Create pipeline
                llm, embed = ProviderRouter.get_providers(
                    llm_provider_name=llm_provider,
                    embed_provider_name=embed_provider,
                    mode=mode
                )

                st.session_state.pipeline = RAGPipeline(
                    llm_provider=llm,
                    embed_provider=embed,
                    workspace_id=workspace_id
                )

                # Update policy settings
                st.session_state.pipeline.policy.hybrid_safe_mode = hybrid_safe
                st.session_state.pipeline.policy.max_snippet_length = max_snippet_length

                st.success(f"✅ Pipeline initialized: {llm_provider.upper()} + {embed_provider.upper()}")

            except Exception as e:
                st.error(f"❌ Initialization failed: {str(e)}")

    # Status indicator
    if st.session_state.pipeline:
        st.success("🟢 Pipeline Active")
        st.caption(f"Workspace: `{st.session_state.workspace_id}`")
        st.caption(f"Mode: `{mode}`")
        st.caption(f"LLM: `{llm_provider}`")
        st.caption(f"Embeddings: `{embed_provider}`")
    else:
        st.warning("🟡 Pipeline Not Initialized")


# --- Main Content ---
st.title("🧠 NEXUS - Hybrid Cloud RAG")
st.markdown("**Autonomous Document Intelligence** with multi-provider support")

# Check if pipeline is ready
if not st.session_state.pipeline:
    st.info("👈 Initialize the pipeline in the sidebar to get started")
    st.stop()

pipeline = st.session_state.pipeline


# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📄 Index Documents", "💬 Query", "📊 Analytics", "🔍 Run Ledger"])


# --- Tab 1: Index Documents ---
with tab1:
    st.header("Index Documents")

    col1, col2 = st.columns([2, 1])

    with col1:
        # File upload
        uploaded_files = st.file_uploader(
            "Upload documents (PDF, TXT, MD)",
            type=["pdf", "txt", "md"],
            accept_multiple_files=True,
            help="Upload documents to index into the knowledge base"
        )

        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} file(s) ready to index")

            if st.button("🚀 Index Documents", type="primary"):
                with st.spinner("Indexing documents..."):
                    # Save uploaded files temporarily
                    temp_dir = Path("./temp_uploads")
                    temp_dir.mkdir(exist_ok=True)

                    file_paths = []
                    for uploaded_file in uploaded_files:
                        file_path = temp_dir / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        file_paths.append(str(file_path))

                    try:
                        # Index documents
                        index_request = IndexRequest(
                            paths=file_paths,
                            workspace_id=st.session_state.workspace_id
                        )

                        start_time = time.time()
                        result = pipeline.index_documents(index_request)
                        elapsed = time.time() - start_time

                        # Display results
                        st.success(f"✅ Indexing complete in {elapsed:.2f}s")

                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("Files Processed", result.files_processed)
                        col_b.metric("Total Chunks", result.total_chunks)
                        col_c.metric("Processing Time", f"{result.processing_time_ms:.0f}ms")

                        # Show document sources
                        with st.expander("📋 Indexed Documents"):
                            for source in result.document_sources:
                                st.text(f"• {source.file_path}")
                                st.caption(f"  Hash: {source.file_hash[:12]}... | Modified: {source.file_mtime}")

                    except Exception as e:
                        st.error(f"❌ Indexing failed: {str(e)}")

    with col2:
        st.subheader("Indexing Info")
        st.info("""
        **Supported Formats:**
        - PDF documents
        - Text files (.txt)
        - Markdown (.md)

        **Chunking:**
        - Size: 1000 chars
        - Overlap: 200 chars

        **Storage:**
        - Vector DB: ChromaDB
        - Embeddings: Per config
        """)


# --- Tab 2: Query ---
with tab2:
    st.header("Query Knowledge Base")

    # Query input
    question = st.text_area(
        "Ask a question",
        placeholder="What would you like to know?",
        help="Ask questions about your indexed documents",
        height=100
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        max_results = st.slider("Max Results", min_value=1, max_value=10, value=3)

    with col2:
        if st.button("🔍 Search", type="primary", disabled=not question):
            with st.spinner("Searching knowledge base..."):
                try:
                    # Query pipeline
                    query_request = QueryRequest(
                        question=question,
                        workspace_id=st.session_state.workspace_id,
                        max_results=max_results
                    )

                    start_time = time.time()
                    response = pipeline.query(query_request)
                    elapsed = time.time() - start_time

                    # Store in history
                    st.session_state.query_history.append({
                        "question": question,
                        "answer": response.answer,
                        "timestamp": time.time(),
                        "latency_ms": response.latency_ms,
                        "citations": len(response.citations)
                    })

                    # Display answer
                    st.subheader("💡 Answer")
                    st.markdown(response.answer)

                    # Display metrics
                    st.divider()
                    col_a, col_b, col_c, col_d = st.columns(4)
                    col_a.metric("Latency", f"{response.latency_ms:.0f}ms")
                    col_b.metric("Citations", len(response.citations))
                    col_c.metric("Model", response.model_used)
                    col_d.metric("Provider", response.provider.replace("LLMProvider", ""))

                    # Display citations
                    st.subheader("📚 Citations")
                    for i, citation in enumerate(response.citations, 1):
                        with st.expander(f"Citation {i} - {citation.source}"):
                            st.text(f"Page: {citation.page or 'N/A'}")
                            st.text(f"Relevance: {citation.relevance_score:.2f}")
                            st.markdown(f"**Excerpt:**\n\n{citation.excerpt}")
                            st.caption(f"Hash: {citation.content_hash[:12]}...")

                    # Show run ID
                    st.caption(f"Run ID: `{response.run_id}`")

                except Exception as e:
                    st.error(f"❌ Query failed: {str(e)}")

    # Query history
    if st.session_state.query_history:
        st.divider()
        st.subheader("📜 Query History")

        for i, query in enumerate(reversed(st.session_state.query_history[-5:]), 1):
            with st.expander(f"{i}. {query['question'][:60]}..."):
                st.markdown(f"**Answer:** {query['answer'][:200]}...")
                st.caption(f"⏱️ {query['latency_ms']:.0f}ms | 📚 {query['citations']} citations")


# --- Tab 3: Analytics ---
with tab3:
    st.header("Workspace Analytics")

    try:
        # Get workspace stats from ledger
        stats = pipeline.ledger.get_workspace_stats(st.session_state.workspace_id)

        # Index stats
        st.subheader("📥 Indexing Stats")
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Index Runs", stats["index_runs"]["total"])
        col2.metric("Files Indexed", stats["index_runs"]["total_files"])
        col3.metric("Total Chunks", stats["index_runs"]["total_chunks"])
        col4.metric("Avg Processing Time", f"{stats['index_runs']['avg_processing_time_ms']:.0f}ms")

        # Query stats
        st.subheader("💬 Query Stats")
        col1, col2, col3 = st.columns(3)

        col1.metric("Total Queries", stats["query_runs"]["total"])
        col2.metric("Avg Latency", f"{stats['query_runs']['avg_latency_ms']:.0f}ms")
        col3.metric("Avg Citations", f"{stats['query_runs']['avg_citations']:.1f}")

        # Policy summary
        st.subheader("🔒 Policy Configuration")
        policy_summary = pipeline.policy.get_policy_summary()

        col1, col2 = st.columns(2)
        col1.metric("Hybrid Safe Mode", "✅ Enabled" if policy_summary["hybrid_safe_mode"] else "❌ Disabled")
        col2.metric("Max Snippet Length", f"{policy_summary['max_snippet_length']} chars")

    except Exception as e:
        st.error(f"❌ Failed to load analytics: {str(e)}")


# --- Tab 4: Run Ledger ---
with tab4:
    st.header("Run Ledger (Audit Trail)")

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        run_type = st.selectbox("Run Type", ["all", "index", "query"])

    with col2:
        limit = st.slider("Limit", min_value=10, max_value=100, value=20)

    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()

    try:
        # Get runs from ledger
        runs = pipeline.ledger.list_runs(
            workspace_id=st.session_state.workspace_id,
            run_type=run_type,
            limit=limit
        )

        # Display index runs
        if run_type in ["all", "index"] and runs["index_runs"]:
            st.subheader("📥 Index Runs")

            for run in runs["index_runs"][:10]:
                with st.expander(f"{run['run_id']} - {run['timestamp']}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Files Processed", run["files_processed"])
                        st.metric("Total Chunks", run["total_chunks"])

                    with col2:
                        st.metric("Processing Time", f"{run['processing_time_ms']:.0f}ms")
                        st.metric("Embed Provider", run["embed_provider"])

        # Display query runs
        if run_type in ["all", "query"] and runs["query_runs"]:
            st.subheader("💬 Query Runs")

            for run in runs["query_runs"][:10]:
                with st.expander(f"{run['run_id']} - {run['timestamp']}"):
                    st.text(f"Question: {run['question'][:100]}...")
                    st.text(f"Answer: {run['answer'][:150]}...")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Latency", f"{run['latency_ms']:.0f}ms")

                    with col2:
                        st.metric("Citations", run["citation_count"])

                    with col3:
                        st.metric("Model", run["model_used"])

    except Exception as e:
        st.error(f"❌ Failed to load runs: {str(e)}")


# --- Footer ---
st.divider()
st.caption(f"NEXUS v1.0 | Workspace: `{st.session_state.workspace_id}` | Mode: `{Config.NEXUS_MODE.value}`")
