
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from datasets import Dataset 
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_vector_store_DB.vector_store_mange import QdrantVectorStoreManager

# Load environment variables
load_dotenv()

def run_evaluation(test_dataset_path: str = "test_dataset.csv", output_file: str = "evaluation_results.csv"):
    """Run evaluation on the test dataset"""
    
    # 1. Load Test Dataset
    if not os.path.exists(test_dataset_path):
        print(f"Test dataset not found at {test_dataset_path}")
        return
    
    df = pd.read_csv(test_dataset_path)
    questions = df['question'].tolist()
    ground_truths = df['ground_truth'].tolist()
    
    # 2. Initialize Vector Store
    print("Initializing Vector Store...")
    vector_store = QdrantVectorStoreManager(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        qdrant_url=os.getenv("QDRANT_URL"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        use_cloud=True # Assuming cloud usage based on previous files, adjust if needed
    )
    
    # 3. generate Answers and Contexts
    answers = []
    contexts = []
    
    print(f"Evaluating {len(questions)} questions...")
    for i, question in enumerate(questions):
        print(f"Processing question {i+1}/{len(questions)}: {question}")
        
        # Search for context
        search_results = vector_store.search(query=question, n_results=3)
        retrieved_contexts = [res['content'] for res in search_results]
        contexts.append(retrieved_contexts)
        
        # Generate Answer
        answer_text = vector_store.generate_response(
            query=question,
            context_docs=search_results
        )
        answers.append(answer_text)
        
    # 4. Prepare Dataset for Ragas
    data = {
        'question': questions,
        'answer': answers,
        'contexts': contexts,
        'ground_truth': ground_truths
    }
    dataset = Dataset.from_dict(data)
    
    # 5. Configure Metrics and LLM
    # Use Groq for evaluation metrics that require an LLM
    groq_api_key = os.getenv("GROQ_API_KEY")
    evaluator_llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name="llama-3.3-70b-versatile"
    )
    embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
    
    # metrics = [
    #     faithfulness,
    #     answer_relevancy,
    #     context_precision,
    #     context_recall,
    # ]
    
    # 6. Run Evaluation
    print("Running Ragas Evaluation...")
    results = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=evaluator_llm,
        embeddings=embeddings
    )
    
    # 7. Save Results
    print(results)
    results_df = results.to_pandas()
    results_df.to_csv(output_file, index=False)
    print(f"Evaluation results saved to {output_file}")
    
    return results

if __name__ == "__main__":
    run_evaluation()
