from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from qa_data import knowledge_base

# Load a pre-trained sentence model. This model is small but very effective.
model = SentenceTransformer('all-MiniLM-L6-v2')

# Convert the knowledge base questions into embeddings.
kb_sentences = [item['question'] for item in knowledge_base]
kb_embeddings = model.encode(kb_sentences)

# Build a FAISS index for efficient searching. This is the key to scalability.
index = faiss.IndexFlatL2(kb_embeddings.shape[1])
index.add(np.array(kb_embeddings))

# In your nlp_utils.py, find the get_answer function and replace it.
def get_answer(query_text):
    # Convert the user's query into an embedding.
    query_embedding = model.encode([query_text])

    # Search the FAISS index for the most similar question.
    D, I = index.search(np.array(query_embedding), k=1)

    # Get the index of the most similar question.
    best_match_index = I[0][0]
    answer_data = knowledge_base[best_match_index]

    return {
        "answer": answer_data['answer'],
        "confidence": float(1.0 - D[0][0]),
        # Return the new recommendations list
        "recommendations": answer_data['recommendations']
    }