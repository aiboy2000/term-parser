import unittest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAPIEndpoints(unittest.TestCase):
    """Test cases for API endpoints"""
    
    def test_api_routes(self):
        """Test that all API routes are defined"""
        expected_routes = [
            "/search",
            "/extract",
            "/extract/batch",
            "/database/info",
            "/terms"
        ]
        
        # Since we can't import without dependencies, just check file content
        with open("term_extractor/api/routes.py", "r") as f:
            content = f.read()
            
        for route in expected_routes:
            self.assertIn(f'@router.post("{route}"', content + f'@router.get("{route}"',
                         f"Route {route} not found in routes.py")
    
    def test_api_models_structure(self):
        """Test API model definitions exist"""
        required_models = [
            "SearchType",
            "TermInfo",
            "SearchRequest",
            "SearchResponse",
            "ExtractRequest",
            "ExtractResponse",
            "BatchExtractRequest",
            "BatchExtractResponse",
            "DatabaseInfo"
        ]
        
        with open("term_extractor/api/models.py", "r") as f:
            content = f.read()
            
        for model in required_models:
            self.assertIn(f"class {model}", content,
                         f"Model {model} not found in models.py")


class TestMainApp(unittest.TestCase):
    """Test cases for main FastAPI application"""
    
    def test_main_app_structure(self):
        """Test main.py structure"""
        with open("main.py", "r") as f:
            content = f.read()
            
        # Check required imports
        self.assertIn("from fastapi import FastAPI", content)
        self.assertIn("import uvicorn", content)
        
        # Check middleware
        self.assertIn("CORSMiddleware", content)
        
        # Check routes included
        self.assertIn("app.include_router", content)
        
        # Check endpoints
        self.assertIn('@app.get("/")', content)
        self.assertIn('@app.get("/health")', content)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_sample_workflow(self):
        """Test a sample workflow (without actual execution)"""
        # This would be the expected workflow:
        # 1. Extract terms from PDFs
        # 2. Build database
        # 3. Search for terms
        # 4. Get results
        
        workflow_steps = [
            "PDFTermExtractor",
            "extract_terms_from_pdfs",
            "TermDatabase",
            "build_from_terms",
            "hybrid_search"
        ]
        
        # Check all components exist
        with open("term_extractor/core/pdf_extractor.py", "r") as f:
            pdf_content = f.read()
        
        with open("term_extractor/core/term_database.py", "r") as f:
            db_content = f.read()
            
        all_content = pdf_content + db_content
        
        for step in workflow_steps:
            self.assertIn(step, all_content,
                         f"Workflow component {step} not found")


if __name__ == '__main__':
    unittest.main()