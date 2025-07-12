import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from whoosh import index, fields, qparser
from whoosh.filedb.filestore import FileStorage
import logging

logger = logging.getLogger(__name__)


class TermDatabase:
    def __init__(self, db_path: Path = Path("./data/term_db")):
        self.db_path = db_path
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize sentence transformer for Japanese
        self.encoder = SentenceTransformer('sonoisa/sentence-bert-base-ja-mean-tokens-v2')
        
        # Initialize Faiss index
        self.vector_dim = 768  # Dimension of the sentence transformer
        self.faiss_index = None
        self.terms_data = []
        
        # Initialize Whoosh index
        self.whoosh_index = None
        self._setup_whoosh_index()
    
    def _setup_whoosh_index(self):
        """Setup Whoosh full-text search index"""
        schema = fields.Schema(
            id=fields.ID(stored=True),
            term=fields.TEXT(stored=True, analyzer=fields.SimpleAnalyzer()),
            aliases=fields.TEXT(stored=True),
            category=fields.TEXT(stored=True),
            context=fields.TEXT(stored=True)
        )
        
        index_path = self.db_path / "whoosh_index"
        if not index_path.exists():
            index_path.mkdir()
            self.whoosh_index = index.create_in(str(index_path), schema)
        else:
            self.whoosh_index = index.open_dir(str(index_path))
    
    def build_from_terms(self, terms: List[Dict[str, any]]):
        """Build database from extracted terms"""
        logger.info(f"Building database from {len(terms)} terms")
        
        # Initialize Faiss index
        self.faiss_index = faiss.IndexFlatL2(self.vector_dim)
        
        # Prepare data
        writer = self.whoosh_index.writer()
        vectors = []
        
        for idx, term_info in enumerate(terms):
            # Enhance term data
            term_data = {
                'id': idx,
                'term': term_info['term'],
                'aliases': self._generate_aliases(term_info['term']),
                'category': self._categorize_term(term_info['term']),
                'confidence': term_info.get('confidence', 0.8),
                'frequency': term_info.get('frequency', 1),
                'context': ''  # Can be enhanced with surrounding text
            }
            
            self.terms_data.append(term_data)
            
            # Generate vector embedding
            vector = self.encoder.encode(term_data['term'])
            vectors.append(vector)
            
            # Add to Whoosh index
            writer.add_document(
                id=str(idx),
                term=term_data['term'],
                aliases=' '.join(term_data['aliases']),
                category=term_data['category'],
                context=term_data['context']
            )
        
        # Add vectors to Faiss
        vectors_np = np.array(vectors).astype('float32')
        self.faiss_index.add(vectors_np)
        
        # Commit Whoosh changes
        writer.commit()
        
        # Save database
        self.save()
        
        logger.info("Database built successfully")
    
    def _generate_aliases(self, term: str) -> List[str]:
        """Generate possible aliases for a term"""
        aliases = []
        
        # Common abbreviations for construction terms
        abbreviation_map = {
            '鉄筋コンクリート': ['RC', '鉄コン'],
            'プレストレストコンクリート': ['PC'],
            '鉄骨鉄筋コンクリート': ['SRC'],
            '空調設備': ['空調', 'エアコン', 'AC'],
            '給排水設備': ['給排水'],
        }
        
        if term in abbreviation_map:
            aliases.extend(abbreviation_map[term])
        
        # Add variations without particles
        if 'の' in term:
            aliases.append(term.replace('の', ''))
        
        return aliases
    
    def _categorize_term(self, term: str) -> str:
        """Categorize construction term"""
        categories = {
            '構造': ['鉄筋', 'コンクリート', '鉄骨', '基礎', '柱', '梁', '耐震'],
            '設備': ['空調', '給排水', '電気', '配管', '配線', '消防'],
            '仕上げ': ['塗装', 'タイル', 'クロス', '床', '天井', '壁'],
            '材料': ['セメント', '鋼材', '木材', '石材', 'ガラス'],
            '施工': ['工事', '施工', '工程', '現場', '作業'],
            '管理': ['品質', '安全', '工程', '検査', '試験']
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in term:
                    return category
        
        return '一般'
    
    def search_vector(self, query: str, k: int = 10) -> List[Dict[str, any]]:
        """Search using vector similarity"""
        if self.faiss_index is None:
            return []
        
        # Encode query
        query_vector = self.encoder.encode(query).astype('float32').reshape(1, -1)
        
        # Search
        distances, indices = self.faiss_index.search(query_vector, k)
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.terms_data):
                result = self.terms_data[idx].copy()
                result['score'] = float(1 / (1 + distance))  # Convert distance to similarity
                results.append(result)
        
        return results
    
    def search_text(self, query: str, limit: int = 10) -> List[Dict[str, any]]:
        """Search using full-text search"""
        results = []
        
        with self.whoosh_index.searcher() as searcher:
            # Search in multiple fields
            query_parser = qparser.MultifieldParser(
                ["term", "aliases", "category"], 
                self.whoosh_index.schema
            )
            q = query_parser.parse(query)
            
            search_results = searcher.search(q, limit=limit)
            
            for hit in search_results:
                idx = int(hit['id'])
                if idx < len(self.terms_data):
                    result = self.terms_data[idx].copy()
                    result['score'] = hit.score
                    results.append(result)
        
        return results
    
    def hybrid_search(self, query: str, k: int = 10, alpha: float = 0.5) -> List[Dict[str, any]]:
        """Hybrid search combining vector and text search"""
        # Get results from both methods
        vector_results = self.search_vector(query, k * 2)
        text_results = self.search_text(query, k * 2)
        
        # Combine results
        combined_scores = {}
        all_terms = set()
        
        # Process vector results
        for result in vector_results:
            term = result['term']
            all_terms.add(term)
            combined_scores[term] = alpha * result['score']
        
        # Process text results
        for result in text_results:
            term = result['term']
            all_terms.add(term)
            if term in combined_scores:
                combined_scores[term] += (1 - alpha) * result['score']
            else:
                combined_scores[term] = (1 - alpha) * result['score']
        
        # Create final results
        final_results = []
        for term in all_terms:
            term_data = next((t for t in self.terms_data if t['term'] == term), None)
            if term_data:
                result = term_data.copy()
                result['score'] = combined_scores[term]
                final_results.append(result)
        
        # Sort by score
        final_results.sort(key=lambda x: x['score'], reverse=True)
        
        return final_results[:k]
    
    def save(self):
        """Save database to disk"""
        # Save Faiss index
        if self.faiss_index is not None:
            faiss.write_index(self.faiss_index, str(self.db_path / "faiss.index"))
        
        # Save terms data
        with open(self.db_path / "terms_data.pkl", 'wb') as f:
            pickle.dump(self.terms_data, f)
        
        # Save metadata
        metadata = {
            'num_terms': len(self.terms_data),
            'vector_dim': self.vector_dim
        }
        with open(self.db_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """Load database from disk"""
        try:
            # Load Faiss index
            faiss_path = self.db_path / "faiss.index"
            if faiss_path.exists():
                self.faiss_index = faiss.read_index(str(faiss_path))
            
            # Load terms data
            terms_path = self.db_path / "terms_data.pkl"
            if terms_path.exists():
                with open(terms_path, 'rb') as f:
                    self.terms_data = pickle.load(f)
            
            logger.info(f"Loaded database with {len(self.terms_data)} terms")
            
        except Exception as e:
            logger.error(f"Error loading database: {e}")
    
    def get_all_terms(self) -> List[Dict[str, any]]:
        """Get all terms in database"""
        return self.terms_data.copy()