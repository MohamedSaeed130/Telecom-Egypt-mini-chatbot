import streamlit as st
import os
import sys
import time
import tempfile
import shutil
from langdetect import detect

# Add src to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qdrant_vector_store_DB.vector_store_mange import QdrantVectorStoreManager
from data_extraction.data_extraction_docs.docs_processing import TelecomEgyptDocumentProcessor
from data_indexer.data_indexing import DocumentIndexer

# --- Page Config ---
st.set_page_config(
    page_title="WE Intelligent Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Main Background and Text */
    .stApp {
        background-color: #f8f9fa;
        color: #333333;
    }
    
    /* Header Styling */
    .header-container {
        padding: 1rem 0;
        text-align: center;
        background: linear-gradient(90deg, #5a2d81 0%, #3e1b5e 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        font-size: 1rem;
        opacity: 0.9;
    }

    /* Chat Message Styling */
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    /* User Message */
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #e0e0e0; /* Light Gray for user */
        color: #333333;
    }
    
    /* Assistant Message */
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #f3e5f5; /* Light Purple for assistant */
        border-left: 5px solid #5a2d81;
        color: #333333;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
    
    /* Button Styling */
    .stButton button {
        background-color: #5a2d81;
        color: white;
        border-radius: 5px;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton button:hover {
        background-color: #7b45a8;
    }
    
    /* File Uploader */
    .stFileUploader {
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="header-container">
    <h1 class="header-title">Telecom Egypt Assistant</h1>
    <p class="header-subtitle">Your AI-powered guide to WE services and packages</p>
</div>
""", unsafe_allow_html=True)

# --- Initialization ---
@st.cache_resource
def get_vector_store():
    # Credentials
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    try:
        store = QdrantVectorStoreManager(
            groq_api_key=GROQ_API_KEY,
            collection_name="telecom_egypt_VDB",
            embedding_model_name="intfloat/multilingual-e5-large",
            use_cloud=True, 
            qdrant_url=QDRANT_URL,
            qdrant_api_key=QDRANT_API_KEY
        )
        return store
    except Exception as e:
        st.error(f"Failed to connect to Knowledge Base: {e}")
        return None

vector_store = get_vector_store()

# uploading files
def process_and_index_file(uploaded_file):
    if vector_store:
        with st.spinner(f"Processing & Indexing {uploaded_file.name}..."):
            try:
                # Create a temporary directory
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save uploaded file
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process document
                    processor = TelecomEgyptDocumentProcessor()
                    output_json_path = os.path.join(temp_dir, "processed_doc.json")
                    
                    # process_multiple_documents takes list of paths
                    processor.process_multiple_documents([file_path], output_json_path)
                    
                    # Index document
                    indexer = DocumentIndexer(vector_store)
                    
                    if os.path.exists(output_json_path):
                        # Use existing method to index from json
                        result = indexer.index_uploaded_documents(output_json_path)
                        
                        if isinstance(result, str) and result.startswith("Error"):
                            st.error(result)
                        else:
                            st.success(f"Successfully added **{uploaded_file.name}** to the knowledge base!")
                    else:
                        st.warning("No content extracted from the file.")
                        
            except Exception as e:
                st.error(f"Error processing file: {e}")
    else:
        st.error("Vector Store not available, cannot index.")

def detect_language(text: str) -> str:
        """Detect language of text"""
        try:
            lang = detect(text)
            return lang if lang in ['ar', 'en'] else 'en'
        except:
            return "en"

# --- Sidebar ---
with st.sidebar:
    st.image("https://www.te.eg/TEStaticThemeResidential8/themes/Portal8.0/css/tedata/images/svgfallback/logo.png", width=100)
    st.markdown("### about")
    st.info(
        "This intelligent assistant uses **RAG (Retrieval-Augmented Generation)** "
        "to provide accurate answers from Telecom Egypt's official documentation."
    )
    
    st.markdown("---")
    st.markdown("### 📤 Upload Knowledge")
    uploaded_file = st.file_uploader("Add a document (PDF, DOCX, TXT,PNG,JPG)", type=['pdf', 'docx', 'txt', 'html','png','jpg'])
    if uploaded_file is not None:
        if st.button("Process & Index"):
            process_and_index_file(uploaded_file)
    
    st.markdown("---")
    st.caption("Powered by Groq & Qdrant")


# --- Chat Logic ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome! I can help you with internet packages, mobile plans, and more. How can I assist you today?"}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about WE services..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    if vector_store:
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:    
                    search_results = vector_store.search(
                        query=prompt,
                        n_results=6, 
                        filter_metadata=None #search all sources (web + upload)
                    )
                
                    response_text = vector_store.generate_response(
                        query=prompt,
                        context_docs=search_results,
                        language=detect_language(prompt)
                    )
                    
                    st.markdown(response_text)
                    
                    # Add to history
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                    # Show sources in expander
                    with st.expander("View Sources"):
                        for i, res in enumerate(search_results, 1):
                            source_name = res['metadata'].get('title', 'Unknown')
                            # If uploaded file, title might not be there, check filename or source
                            if res['metadata'].get('source') == 'upload':
                                source_name = res['metadata'].get('filename', 'Uploaded Document')
                            
                            st.markdown(f"**Source {i}:** {source_name}")
                            st.caption(res['content'][:200] + "...")
                            if 'url' in res['metadata']:
                                st.markdown(f"[Link]({res['metadata']['url']})")
                                
                except Exception as e:
                    st.error(f"An error occurred: {e}")
    else:
        st.error("Vector Store not initialized.")
