"""
Core RAG pipeline - headless operation.
Orchestrates document indexing, retrieval, and answer generation.
"""
import time
import hashlib
import uuid
from typing import List, Optional
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from .config import Config
from .models import (
    QueryRequest, QueryResponse, Citation,
    IndexRequest, IndexResult, DocumentSource
)
from .providers.base import LLMProvider, EmbeddingProvider
from .router import ProviderRouter
from .policy import PolicyRedactor


class RAGPipeline:
    """
    Headless RAG pipeline for NEXUS.
    Can be used by UI, API, or CLI.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        embed_provider: Optional[EmbeddingProvider] = None,
        workspace_id: str = "default"
    ):
        """
        Initialize RAG pipeline with providers.

        Args:
            llm_provider: LLM provider (defaults to router selection)
            embed_provider: Embedding provider (defaults to router selection)
            workspace_id: Workspace identifier for isolation
        """
        self.workspace_id = workspace_id

        # Use router to get providers if not explicitly provided
        if llm_provider is None or embed_provider is None:
            llm, embed = ProviderRouter.get_providers()
            self.llm_provider = llm_provider or llm
            self.embed_provider = embed_provider or embed
        else:
            self.llm_provider = llm_provider
            self.embed_provider = embed_provider

        # Initialize policy redactor for hybrid safety
        self.policy = PolicyRedactor()

        # Initialize vector store path for this workspace
        self.chroma_path = f"{Config.CHROMA_DB_PATH}/{workspace_id}"

        # Lazy-loaded components
        self._vectorstore = None
        self._retriever = None

    def _get_vectorstore(self):
        """Lazy load vector store"""
        if self._vectorstore is None:
            import os
            if os.path.exists(self.chroma_path) and os.listdir(self.chroma_path):
                # Load existing
                self._vectorstore = Chroma(
                    persist_directory=self.chroma_path,
                    embedding_function=self.embed_provider._get_embeddings()
                )
            else:
                # Will be created on first index
                pass
        return self._vectorstore

    def index_documents(self, request: IndexRequest) -> IndexResult:
        """
        Index documents into vector store.

        Args:
            request: Index request with file paths

        Returns:
            IndexResult with stats
        """
        start_time = time.time()

        # Load documents
        from langchain_community.document_loaders import PyPDFLoader, TextLoader
        import os

        documents = []
        sources = []

        for file_path in request.paths:
            if not os.path.exists(file_path):
                continue

            # Load based on extension
            if file_path.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file_path.endswith((".txt", ".md")):
                loader = TextLoader(file_path)
            else:
                continue

            docs = loader.load()
            documents.extend(docs)

            # Track source
            sources.append(DocumentSource(
                file_path=file_path,
                file_hash=self._hash_file(file_path),
                file_mtime=os.path.getmtime(file_path),
                indexed_at=datetime.now()
            ))

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        splits = text_splitter.split_documents(documents)

        # Create or update vector store
        if self._vectorstore is None:
            self._vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embed_provider._get_embeddings(),
                persist_directory=self.chroma_path
            )
        else:
            # Add to existing
            self._vectorstore.add_documents(splits)

        processing_time = (time.time() - start_time) * 1000

        return IndexResult(
            workspace_id=self.workspace_id,
            files_processed=len(request.paths),
            files_skipped=0,
            total_chunks=len(splits),
            processing_time_ms=processing_time,
            document_sources=sources
        )

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Query the knowledge base.

        Args:
            request: Query request

        Returns:
            QueryResponse with answer and citations
        """
        start_time = time.time()
        run_id = str(uuid.uuid4())

        # Get retriever
        vectorstore = self._get_vectorstore()
        if vectorstore is None:
            raise ValueError("No documents indexed yet")

        retriever = vectorstore.as_retriever(search_kwargs={"k": request.max_results})

        # Retrieve relevant documents
        docs = retriever.get_relevant_documents(request.question)

        # Build citations with FULL excerpts (pre-redaction)
        citations = []
        for i, doc in enumerate(docs):
            citations.append(Citation(
                source=doc.metadata.get('source', 'unknown'),
                page=doc.metadata.get('page'),
                excerpt=doc.page_content,  # FULL content for redaction
                relevance_score=1.0 / (i + 1),  # Simple relevance
                content_hash=hashlib.md5(doc.page_content.encode()).hexdigest()
            ))

        # Apply policy redaction to get safe snippets
        safe_context, excerpt_hashes = self.policy.redact_snippets(citations)

        # Build prompt
        template = """
        You are NEXUS, an autonomous document intelligence agent.
        Use the following context to answer the question accurately and concisely.
        If you don't know, say so.

        Context: {context}

        Question: {question}

        Answer:
        """
        prompt = ChatPromptTemplate.from_template(template)

        # Generate answer with SAFE context (not full docs)
        formatted_prompt = prompt.format(context=safe_context, question=request.question)

        # Validate outbound payload (safety check)
        if not self.policy.validate_outbound_payload(formatted_prompt):
            raise ValueError("Policy violation: Outbound payload failed safety check")

        answer = self.llm_provider.generate(formatted_prompt)

        # Truncate citation excerpts to first 200 chars for response
        for citation in citations:
            citation.excerpt = citation.excerpt[:200]

        latency = (time.time() - start_time) * 1000

        return QueryResponse(
            answer=answer,
            citations=citations,
            workspace_id=self.workspace_id,
            model_used=self.llm_provider.get_model_name(),
            provider=type(self.llm_provider).__name__,
            latency_ms=latency,
            run_id=run_id,
            timestamp=datetime.now()
        )

    def _hash_file(self, file_path: str) -> str:
        """Generate hash of file contents"""
        import hashlib
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
