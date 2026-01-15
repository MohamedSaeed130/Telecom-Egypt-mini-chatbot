# 🤖 Telecom-Egypt-mini-chatbot ![Telecom Egypt Logo](https://www.te.eg/TEStaticThemeResidential8/themes/Portal8.0/css/tedata/images/svgfallback/logo.png) 

A production-ready RAG-powered intelligent chatbot for Telecom Egypt that answers customer questions using the official website as the primary knowledge base.

## Demo
## 📹 [Project Demo](https://drive.google.com/file/d/17S9ZSUy5_YWJ3f8Ag6FAwryOKCMahAs1/view?usp=drive_link)
## Presentation
# [Project Presentation](https://docs.google.com/presentation/d/1IO0PKryle-aG4T-NFOhgu5t2ec8QYF_Q/edit?usp=drive_link&ouid=108481101390315748319&rtpof=true&sd=true)

## Key Features

- **Multi-lingual Support**: Handles Arabic (Modern Standard & Egyptian dialect) and English
- **RAG-Powered**: Uses Retrieval Augmented Generation for accurate, grounded responses
- **Document Upload**: Supports PDF, DOCX, TXT, HTML, and images (with OCR)
- **Source Citations**: All answers include references to original sources
- **Web-Based Interface**: Professional Streamlit chat interface

## Tech Stack
- **Frontend**: [Streamlit](https://streamlit.io/)
- **LLM**: [Groq API](https://groq.com/) (llama-3.3-70b-versatile)
- **Vector DB**: [Qdrant Cloud](https://qdrant.tech/)
- **Embeddings**: HuggingFace (`intfloat/multilingual-e5-large`)
- **Scraping**: [Scrapy](https://scrapy.org/)
- **Document Processing**: `PyPDF2`, `python-docx`, `BeautifulSoup`

## Project Structure

```
Telecom-Egypt-mini-chatbot/
├── src/
│   ├── data_chunking/                           # Text chunking logic
│   ├── data_extraction/                         # Scrapy and Document processing
│   │   └── data_extraction_scrapy/              # Scrapy project for web scraping
│   │   └── data_extraction_processing/          # Document processing logic
│   ├── data_indexer/                            # Logic to index data into Qdrant
│   ├── qdrant_vector_store_DB/                  # Qdrant client manager
│   ├── streamlit_app.py                         # Main Streamlit Application UI
│   ├── main_setup.py                            # Script for setup and scraping pipeline
│   ├── requirements.txt                         # Python dependencies
│   └── qdrant_db/                               # Local fallback for vector store
├── LICENSE                                      # License file
└── README.md                                    # Project Documentation
```

## Prerequisites

- Python 3.8+
- Miniconda or Anaconda
- WSL2
- Ubuntu 24.04.1 LTS

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/MohamedSaeed130/Telecom-Egypt-mini-chatbot.git
   cd Telecom-Egypt-mini-chatbot
   cd src
   ```

2. **Set up a Virtual Environment (Optional but Recommended)**
   ```bash
   conda create -n env_name
   conda activate env_name
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
Ensure you have the necessary API keys. The project is currently configured to use embedded keys for demonstration, but for production, set the following environment variables in a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
```

## Usage

### 1. Run main setup
Launch the main user interface:
```bash
python main_setup.py
```

### 2. Run the Chatbot Application
Launch the main user interface:
```bash
streamlit run streamlit_app.py
```
This will open the application in your browser (usually at `http://localhost:8501`).




