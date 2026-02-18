# RAG Evaluation System

This directory contains tools to evaluate the performance of the Telecom Egypt chatbot using the **Ragas** framework.

## Overview

The evaluation system measures how well your RAG (Retrieval-Augmented Generation) chatbot performs across four key metrics:

1. **Faithfulness**: Is the answer grounded in the retrieved context?
2. **Answer Relevancy**: Is the answer relevant to the question?
3. **Context Precision**: Did we retrieve relevant chunks?
4. **Context Recall**: Did we retrieve all necessary information?

## Files

- **`sample_test_dataset.csv`**: A sample test dataset with 5 questions and ground truth answers
- **`simple_eval.py`**: Simplified evaluation script (requires model download)
- **`run_eval.py`**: Full evaluation script with Ragas metrics
- **`generate_dataset.py`**: Script to generate synthetic test datasets (requires large model download)

## Quick Start

### Option 1: Manual Evaluation (Recommended)

Since the embedding model is large (2.24GB), the easiest way to evaluate is to manually test your chatbot:

1. Open your Streamlit app:
   ```bash
   streamlit run src/streamlit_app.py
   ```

2. Test with the questions from `sample_test_dataset.csv`:
   - "What internet packages does Telecom Egypt offer?"
   - "How can I contact Telecom Egypt customer service?"
   - "What are the available mobile plans?"
   - "How do I upgrade my internet speed?"
   - "What is the coverage area for fiber optic internet?"

3. Manually assess:
   - **Faithfulness**: Does the answer match the sources shown?
   - **Relevancy**: Does it answer the question?
   - **Context Quality**: Are the retrieved sources relevant?

### Option 2: Automated Evaluation

If you want automated metrics, you'll need to ensure the embedding model is already cached:

```bash
# This will download models if not already present
python src/evaluation/simple_eval.py
```

**Note**: First run will download:
- `intfloat/multilingual-e5-large` (2.24GB) - for the vector store
- `sentence-transformers/all-MiniLM-L6-v2` (90MB) - for Ragas metrics

## Creating Your Own Test Dataset

Edit `sample_test_dataset.csv` to add more test cases:

```csv
question,ground_truth
"Your question here","Expected answer here"
```

## Interpreting Results

After running evaluation, you'll get scores from 0.0 to 1.0 for each metric:

- **0.8-1.0**: Excellent
- **0.6-0.8**: Good
- **0.4-0.6**: Fair (needs improvement)
- **0.0-0.4**: Poor (requires attention)

Results are saved to `evaluation_results.csv` with per-question breakdowns.

## Troubleshooting

### Model Download is Slow
The multilingual embedding model is 2.24GB. If download is slow:
- Use manual evaluation (Option 1)
- Or wait for the download to complete (may take hours on slow connections)

### Out of Memory
If you get memory errors:
- Reduce `n_results` in the evaluation script (default is 3)
- Use a smaller test dataset
- Close other applications

## Advanced: Synthetic Dataset Generation

To generate test questions automatically from your documents:

```bash
python src/evaluation/generate_dataset.py
```

This uses your LLM to create questions from the indexed documents. **Warning**: This requires downloading the 2.24GB embedding model and may take significant time.

## Dependencies

All required packages are in `src/requirements.txt`:
- `ragas==0.4.3`
- `langchain-groq==1.1.2`
- `langchain-huggingface==1.2.0`
- `datasets==4.5.0`
- `pandas==2.2.3`
