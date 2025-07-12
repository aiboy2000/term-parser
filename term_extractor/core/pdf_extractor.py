import pdfplumber
import re
from typing import List, Dict, Set
from pathlib import Path
from sudachipy import tokenizer, dictionary
import logging

logger = logging.getLogger(__name__)


class PDFTermExtractor:
    def __init__(self):
        self.tokenizer_obj = dictionary.Dictionary().create()
        self.mode = tokenizer.Tokenizer.SplitMode.C
        
        # Construction industry term patterns
        self.term_patterns = [
            r'[ァ-ヴ]{3,}',  # Katakana terms (3+ chars)
            r'[一-龯]{2,}[工事|施工|構造|材料|設備|管理]',  # Kanji + construction suffix
            r'[A-Z]{2,}',  # Abbreviations (RC, PC, etc.)
            r'\d+[級|種|号|型]',  # Numbered classifications
        ]
        
        # Common construction term components
        self.construction_keywords = {
            '工事', '施工', '構造', '材料', '設備', '管理', '基礎', '躯体',
            '仕上げ', '配管', '配線', '防水', '断熱', '耐震', '免震', '制震',
            '鉄筋', 'コンクリート', '鋼材', '木材', '石材', 'タイル', 'ガラス',
            '建築', '土木', '設計', '監理', '検査', '試験', '品質', '安全'
        }
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
        return text
    
    def extract_terms_from_text(self, text: str) -> List[Dict[str, any]]:
        """Extract construction terms from text"""
        terms = []
        seen_terms = set()
        
        # Pattern-based extraction
        for pattern in self.term_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match not in seen_terms and len(match) >= 2:
                    seen_terms.add(match)
                    terms.append({
                        'term': match,
                        'type': 'pattern',
                        'confidence': 0.7
                    })
        
        # Morphological analysis extraction
        tokens = self.tokenizer_obj.tokenize(text, self.mode)
        
        # Extract noun phrases
        current_phrase = []
        for token in tokens:
            pos = token.part_of_speech()[0]
            
            if pos == '名詞':
                current_phrase.append(token.surface())
            else:
                if len(current_phrase) >= 2:
                    phrase = ''.join(current_phrase)
                    if phrase not in seen_terms and self._is_construction_term(phrase):
                        seen_terms.add(phrase)
                        terms.append({
                            'term': phrase,
                            'type': 'morphological',
                            'confidence': 0.8
                        })
                current_phrase = []
        
        # Check last phrase
        if len(current_phrase) >= 2:
            phrase = ''.join(current_phrase)
            if phrase not in seen_terms and self._is_construction_term(phrase):
                terms.append({
                    'term': phrase,
                    'type': 'morphological',
                    'confidence': 0.8
                })
        
        return terms
    
    def _is_construction_term(self, term: str) -> bool:
        """Check if term is likely construction-related"""
        # Check if term contains construction keywords
        for keyword in self.construction_keywords:
            if keyword in term:
                return True
        
        # Check if term is mostly katakana (foreign technical terms)
        katakana_ratio = sum(1 for c in term if 'ァ' <= c <= 'ヴ') / len(term)
        if katakana_ratio > 0.7:
            return True
        
        # Check if term contains numbers with units
        if re.search(r'\d+[mm|cm|m|kg|t|N|Pa|MPa|級|種|号]', term):
            return True
        
        return False
    
    def extract_terms_from_pdfs(self, pdf_folder: Path) -> List[Dict[str, any]]:
        """Extract terms from all PDFs in folder"""
        all_terms = []
        term_frequency = {}
        
        pdf_files = list(pdf_folder.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        for pdf_path in pdf_files:
            logger.info(f"Processing {pdf_path.name}")
            text = self.extract_text_from_pdf(pdf_path)
            terms = self.extract_terms_from_text(text)
            
            # Count frequency
            for term_info in terms:
                term = term_info['term']
                if term in term_frequency:
                    term_frequency[term] += 1
                else:
                    term_frequency[term] = 1
                    all_terms.append(term_info)
        
        # Add frequency information
        for term_info in all_terms:
            term_info['frequency'] = term_frequency[term_info['term']]
            # Boost confidence based on frequency
            if term_info['frequency'] > 3:
                term_info['confidence'] = min(1.0, term_info['confidence'] + 0.1)
        
        # Sort by frequency and confidence
        all_terms.sort(key=lambda x: (x['frequency'], x['confidence']), reverse=True)
        
        return all_terms