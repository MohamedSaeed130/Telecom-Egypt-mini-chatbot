# Telecom-Egypt-mini-chatbot

A production-ready RAG-powered intelligent chatbot for Telecom Egypt that answers customer questions using the official website as the primary knowledge base.

## Features

- **Multi-lingual Support**: Handles Arabic (Modern Standard & Egyptian dialect) and English
- **RAG-Powered**: Uses Retrieval Augmented Generation for accurate, grounded responses
- **Document Upload**: Supports PDF, DOCX, TXT, HTML, and images (with OCR)
- **Source Citations**: All answers include references to original sources
- **Web-Based Interface**: Professional Streamlit chat interface


## Prerequisites

- Python 3.8+
- Miniconda or Anaconda

## Project Structure

```
Telecom-Egypt-mini-chatbot/
│
├── app.py                      # Main Streamlit application
├── setup.py                    # Setup and initialization script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
│
├── scraper.py                  # Web scraping module
├── document_processor.py       # Document processing (PDF, DOCX, etc.)
├── vector_store.py            # Vector database management
├── rag_engine.py              # RAG pipeline and LLM integration
│
├── chroma_db/                 # Vector database storage (auto-created)
└── telecom_egypt_data.json    # Scraped website data (auto-created)
```


export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
