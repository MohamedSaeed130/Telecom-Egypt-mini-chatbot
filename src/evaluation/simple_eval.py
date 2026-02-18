"""
Simple RAG Evaluation Script
Evaluates the chatbot using Ragas metrics without requiring synthetic dataset generation
"""
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
from langchain_huggingface import HuggingFaceEmbeddings

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_vector_store_DB.vector_store_mange import QdrantVectorStoreManager

# Load environment variables
load_dotenv()

def run_simple_evaluation(test_dataset_path: str = "sample_test_dataset.csv", output_file: str = "evaluation_results.csv"):
    """Run evaluation on a simple test dataset"""
    
    print("="*60)
    print("RAG EVALUATION SYSTEM")
    print("="*60)
    
    # 1. Load Test Dataset
    test_dataset_full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), test_dataset_path)
    if not os.path.exists(test_dataset_full_path):
        print(f"❌ Test dataset not found at {test_dataset_full_path}")
        return
    
    print(f"\n📂 Loading test dataset from: {test_dataset_path}")
    df = pd.read_csv(test_dataset_full_path)
    questions = df['question'].tolist()
    ground_truths = df['ground_truth'].tolist()
    print(f"✓ Loaded {len(questions)} test questions")
    
    # 2. Initialize Vector Store
    print("\n🔧 Initializing Vector Store...")
    try:
        vector_store = QdrantVectorStoreManager(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            qdrant_url=os.getenv("QDRANT_URL"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY"),
            collection_name="telecom_egypt_VDB",
            use_cloud=True
        )
        print("✓ Vector store initialized")
    except Exception as e:
        print(f"❌ Failed to initialize vector store: {e}")
        return
    
    # 3. Generate Answers and Contexts
    print("\n🤖 Generating answers for test questions...")
    answers = []
    contexts = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] Processing: {question[:60]}...")
        
        try:
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
            print(f"  ✓ Answer generated ({len(answer_text)} chars)")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            answers.append("Error generating answer")
            contexts.append([])
    
    # 4. Prepare Dataset for Ragas
    print("\n📊 Preparing evaluation dataset...")
    data = {
        'question': questions,
        'answer': answers,
        'contexts': contexts,
        'ground_truth': ground_truths
    }
    dataset = Dataset.from_dict(data)
    print("✓ Dataset prepared")
    
    # 5. Configure Metrics and LLM
    print("\n⚙️  Configuring evaluation metrics...")
    groq_api_key = os.getenv("GROQ_API_KEY")
    evaluator_llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name="llama-3.3-70b-versatile"
    )
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    print("✓ Metrics configured")
    
    # 6. Run Evaluation
    print("\n🔍 Running Ragas Evaluation...")
    print("This may take a few minutes...")
    
    try:
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
        
        print("\n" + "="*60)
        print("EVALUATION RESULTS")
        print("="*60)
        print(results)
        
        # 7. Save Results
        results_df = results.to_pandas()
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
        results_df.to_csv(output_path, index=False)
        print(f"\n✓ Detailed results saved to: {output_file}")
        
        # Print summary statistics
        print("\n📈 SUMMARY STATISTICS:")
        print("-" * 60)
        for metric in ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']:
            if metric in results_df.columns:
                mean_score = results_df[metric].mean()
                print(f"  {metric.replace('_', ' ').title()}: {mean_score:.3f}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    run_simple_evaluation()
