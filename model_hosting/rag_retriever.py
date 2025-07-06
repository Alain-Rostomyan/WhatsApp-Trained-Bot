import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

class RAGRetriever:
    """Simple TF-IDF based retriever."""
    def __init__(self, knowledge_file="../knowledge/knowledge.txt", top_k=3):
        self.knowledge_file = os.path.join(os.path.dirname(__file__), knowledge_file)
        self.top_k = top_k
        self.docs = self._load_docs()
        if self.docs:
            self.vectorizer = TfidfVectorizer(stop_words="english")
            self.doc_matrix = self.vectorizer.fit_transform(self.docs)
            self.nbrs = NearestNeighbors(n_neighbors=self.top_k, metric="cosine").fit(self.doc_matrix)
        else:
            self.vectorizer = None
            self.nbrs = None

    def _load_docs(self):
        if not os.path.exists(self.knowledge_file):
            return []
        with open(self.knowledge_file, "r", encoding="utf-8") as f:
            text = f.read()
        docs = [p.strip() for p in text.splitlines() if p.strip()]
        return docs

    def retrieve(self, query):
        if not self.docs:
            return []
        query_vec = self.vectorizer.transform([query])
        distances, indices = self.nbrs.kneighbors(query_vec, n_neighbors=min(self.top_k, len(self.docs)))
        return [self.docs[i] for i in indices[0]]
