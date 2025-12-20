# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Reorganized project structure to comply with MASTER DIRECTORY STANDARDS (2025-10-06)
- Moved all source code to `02-Src/`
- Moved all tests to `03-Tests/`
- Moved scripts to `05-Scripts/`
- Created standardized directory structure (01-Docs, 02-Src, 03-Tests, etc.)
- Added `.directory-standards.md` reference file
- Updated README.md and created CLAUDE.md with directory standards references
- Removed legacy empty directories (archive, completed-docs, docs, documents, working-mds, professional-templates)

## [1.0.0] - 2024-09-16

### Added
- Initial release of NEXUS Local RAG AI Agent
- Streamlit web interface for document Q&A
- Ollama integration for local LLM inference
- ChromaDB vector database for semantic search
- LangChain RAG pipeline orchestration
- Multi-format document support (PDF, TXT, MD, DOCX, HTML)
- Performance optimization features (caching, parallel processing)
- One-line installer script
- Comprehensive documentation and README
- Test suite with pytest
- GitHub Actions CI/CD pipeline

### Features
- 100% local processing (no cloud dependencies)
- Sub-second query responses
- Supports 100K+ documents
- GDPR/HIPAA compliant architecture
- Air-gap capable operation
- Real-time performance metrics

---

**Note**: This changelog was created as part of directory standardization on 2025-10-06. Previous changes may not be fully documented.
