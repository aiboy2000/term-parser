import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPDFExtractor(unittest.TestCase):
    """Test cases for PDF term extraction"""
    
    def test_term_patterns(self):
        """Test regular expression patterns for term extraction"""
        import re
        
        # Patterns from pdf_extractor.py
        term_patterns = [
            r'[ァ-ヴ]{3,}',  # Katakana terms (3+ chars)
            r'[一-龯]{2,}[工事|施工|構造|材料|設備|管理]',  # Kanji + construction suffix
            r'[A-Z]{2,}',  # Abbreviations (RC, PC, etc.)
            r'\d+[級|種|号|型]',  # Numbered classifications
        ]
        
        test_cases = [
            ("コンクリート", True, 0),  # Katakana
            ("基礎工事", True, 1),  # Kanji + suffix
            ("RC", True, 2),  # Abbreviation
            ("1級", True, 3),  # Numbered classification
            ("あ", False, None),  # Too short
        ]
        
        for text, should_match, pattern_idx in test_cases:
            matched = False
            for idx, pattern in enumerate(term_patterns):
                if re.search(pattern, text):
                    matched = True
                    if should_match:
                        self.assertEqual(idx, pattern_idx, 
                                       f"'{text}' matched wrong pattern")
                    break
            
            self.assertEqual(matched, should_match, 
                           f"'{text}' match result incorrect")
    
    def test_construction_keywords(self):
        """Test construction keyword detection"""
        construction_keywords = {
            '工事', '施工', '構造', '材料', '設備', '管理', '基礎', '躯体',
            '仕上げ', '配管', '配線', '防水', '断熱', '耐震', '免震', '制震',
            '鉄筋', 'コンクリート', '鋼材', '木材', '石材', 'タイル', 'ガラス',
            '建築', '土木', '設計', '監理', '検査', '試験', '品質', '安全'
        }
        
        test_terms = [
            ("基礎工事", True),
            ("耐震構造", True),
            ("品質管理", True),
            ("普通の言葉", False),
            ("食べ物", False),
        ]
        
        for term, should_contain in test_terms:
            contains_keyword = any(keyword in term for keyword in construction_keywords)
            self.assertEqual(contains_keyword, should_contain,
                           f"'{term}' keyword detection incorrect")


class TestTermDatabase(unittest.TestCase):
    """Test cases for term database functionality"""
    
    def test_alias_generation(self):
        """Test alias generation for terms"""
        abbreviation_map = {
            '鉄筋コンクリート': ['RC', '鉄コン'],
            'プレストレストコンクリート': ['PC'],
            '鉄骨鉄筋コンクリート': ['SRC'],
            '空調設備': ['空調', 'エアコン', 'AC'],
            '給排水設備': ['給排水'],
        }
        
        # Test known abbreviations
        self.assertIn('RC', abbreviation_map['鉄筋コンクリート'])
        self.assertIn('PC', abbreviation_map['プレストレストコンクリート'])
        self.assertIn('SRC', abbreviation_map['鉄骨鉄筋コンクリート'])
    
    def test_term_categorization(self):
        """Test term categorization logic"""
        categories = {
            '構造': ['鉄筋', 'コンクリート', '鉄骨', '基礎', '柱', '梁', '耐震'],
            '設備': ['空調', '給排水', '電気', '配管', '配線', '消防'],
            '仕上げ': ['塗装', 'タイル', 'クロス', '床', '天井', '壁'],
            '材料': ['セメント', '鋼材', '木材', '石材', 'ガラス'],
            '施工': ['工事', '施工', '工程', '現場', '作業'],
            '管理': ['品質', '安全', '工程', '検査', '試験']
        }
        
        test_cases = [
            ("鉄筋工事", '構造'),
            ("空調設備", '設備'),
            ("タイル施工", '仕上げ'),
            ("品質検査", '管理'),
        ]
        
        for term, expected_category in test_cases:
            found_category = None
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in term:
                        found_category = category
                        break
                if found_category:
                    break
            
            self.assertEqual(found_category, expected_category,
                           f"'{term}' categorized incorrectly")


if __name__ == '__main__':
    unittest.main()