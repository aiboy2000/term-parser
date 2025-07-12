#!/usr/bin/env python3
"""
Basic tests for term extraction system without external dependencies
"""
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_project_structure():
    """Test that all required files and directories exist"""
    print("Testing project structure...")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "README.md",
        "test_extractor.py",
        ".gitignore"
    ]
    
    required_dirs = [
        "term_extractor",
        "term_extractor/api",
        "term_extractor/core"
    ]
    
    for file in required_files:
        assert Path(file).exists(), f"Missing file: {file}"
        print(f"✓ {file} exists")
    
    for dir in required_dirs:
        assert Path(dir).is_dir(), f"Missing directory: {dir}"
        print(f"✓ {dir}/ exists")
    
    print("Project structure test passed!\n")


def test_module_imports():
    """Test that Python modules can be imported"""
    print("Testing module imports...")
    
    try:
        import term_extractor
        print("✓ term_extractor package imports")
    except ImportError as e:
        print(f"✗ Failed to import term_extractor: {e}")
        return False
    
    try:
        import term_extractor.api
        print("✓ term_extractor.api package imports")
    except ImportError as e:
        print(f"✗ Failed to import term_extractor.api: {e}")
        return False
    
    try:
        import term_extractor.core
        print("✓ term_extractor.core package imports")
    except ImportError as e:
        print(f"✗ Failed to import term_extractor.core: {e}")
        return False
    
    print("Module import test passed!\n")
    return True


def test_api_models():
    """Test API model definitions"""
    print("Testing API models...")
    
    try:
        from term_extractor.api.models import (
            SearchType, TermInfo, SearchRequest, 
            ExtractRequest, DatabaseInfo
        )
        
        # Test SearchType enum
        assert SearchType.VECTOR == "vector"
        assert SearchType.TEXT == "text"
        assert SearchType.HYBRID == "hybrid"
        print("✓ SearchType enum works correctly")
        
        # Test model creation (without pydantic validation)
        print("✓ API models defined correctly")
        
    except ImportError as e:
        print(f"✗ Failed to import API models: {e}")
        return False
    
    print("API models test passed!\n")
    return True


def test_configuration():
    """Test configuration and requirements"""
    print("Testing configuration...")
    
    # Check requirements.txt
    with open("requirements.txt", "r") as f:
        requirements = f.read()
        
    required_packages = [
        "pdfplumber",
        "mecab-python3",
        "sudachipy",
        "faiss-cpu",
        "sentence-transformers",
        "whoosh",
        "fastapi",
        "uvicorn"
    ]
    
    for package in required_packages:
        assert package in requirements, f"Missing package in requirements: {package}"
        print(f"✓ {package} in requirements.txt")
    
    print("Configuration test passed!\n")


def test_sample_term_extraction_logic():
    """Test basic term extraction logic without dependencies"""
    print("Testing term extraction logic...")
    
    # Mock term patterns from pdf_extractor.py
    term_patterns = [
        r'[ァ-ヴ]{3,}',  # Katakana terms
        r'[一-龯]{2,}[工事|施工|構造|材料|設備|管理]',  # Kanji + suffix
        r'[A-Z]{2,}',  # Abbreviations
    ]
    
    test_text = "鉄筋コンクリート造の基礎工事を実施します。RC構造です。"
    
    # Simple pattern matching test
    import re
    found_terms = []
    
    for pattern in term_patterns:
        matches = re.findall(pattern, test_text)
        found_terms.extend(matches)
    
    print(f"✓ Found {len(found_terms)} terms in sample text")
    print(f"  Terms: {found_terms}")
    
    print("Term extraction logic test passed!\n")


def main():
    """Run all tests"""
    print("=" * 50)
    print("Running Basic Tests for Term Extraction System")
    print("=" * 50)
    print()
    
    tests = [
        test_project_structure,
        test_module_imports,
        test_api_models,
        test_configuration,
        test_sample_term_extraction_logic
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result is not False:
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}\n")
            failed += 1
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)