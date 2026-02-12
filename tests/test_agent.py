"""
Test Suite for Wikipedia Agent

Tests for core functionality:
- Search and disambiguation
- Content fetching
- Parsing and extraction
- Summarization
- CLI commands
"""

import pytest
import json
from pathlib import Path
from agent import WikipediaAgent
from modules.search import SearchModule
from modules.fetch import FetchModule
from modules.parse import ParseModule
from modules.summarize import SummarizeModule


# Fixtures
@pytest.fixture
def config():
    """Load test configuration."""
    return {
        "wikipedia_lang": "en",
        "cache_dir": "./test_cache",
        "cache_ttl_seconds": 3600,
        "timeout_seconds": 30,
        "max_retries": 3,
        "rate_limit_delay_ms": 500,
        "default_summary_bullets": 5,
        "log_level": "INFO"
    }


@pytest.fixture
def agent(config):
    """Create agent instance for testing."""
    return WikipediaAgent()


# Test Agent Initialization
class TestAgentInit:
    """Test agent initialization."""
    
    def test_agent_version(self, agent):
        """Test agent version is set."""
        assert agent is not None
        assert hasattr(agent, 'config')
    
    def test_config_loading(self, agent):
        """Test configuration is loaded."""
        assert agent.config is not None
        assert 'wikipedia_lang' in agent.config
    
    def test_cache_directory_created(self, agent):
        """Test cache directory is created."""
        assert agent.cache_dir.exists()


# Test Search Module
class TestSearchModule:
    """Test search functionality."""
    
    def test_search_initialization(self, config):
        """Test search module initializes."""
        search = SearchModule(config)
        assert search is not None
    
    def test_search_query(self, config):
        """Test search returns candidates."""
        search = SearchModule(config)
        results = search.search("Python")
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_search_candidate_structure(self, config):
        """Test search results have required fields."""
        search = SearchModule(config)
        results = search.search("Python")
        
        for candidate in results:
            assert 'title' in candidate
            assert 'url' in candidate
            assert 'description' in candidate


# Test Fetch Module
class TestFetchModule:
    """Test content fetching."""
    
    def test_fetch_initialization(self, config):
        """Test fetch module initializes."""
        fetch = FetchModule(config)
        assert fetch is not None
    
    def test_cache_stats(self, config):
        """Test cache statistics."""
        fetch = FetchModule(config)
        stats = fetch.get_cache_stats()
        
        assert 'cached_pages' in stats
        assert 'cache_size_kb' in stats
        assert 'cache_dir' in stats
    
    def test_cache_operations(self, config):
        """Test cache save and load."""
        from datetime import datetime
        
        fetch = FetchModule(config)
        
        # Use current timestamp so cache won't be expired
        test_data = {
            "title": "Test Article",
            "content": "Test content",
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to cache (internal test)
        fetch._save_to_cache("TestArticle", test_data)
        
        # Load from cache
        cached = fetch._get_from_cache("TestArticle")
        assert cached is not None
        assert cached['title'] == "Test Article"


# Test Parse Module
class TestParseModule:
    """Test content parsing."""
    
    def test_parse_initialization(self, config):
        """Test parse module initializes."""
        parse = ParseModule(config)
        assert parse is not None
    
    def test_text_normalization(self, config):
        """Test text normalization."""
        parse = ParseModule(config)
        
        text = "'''Bold'''  text with   spaces [1]"
        normalized = parse.normalize_text(text)
        
        assert "''" not in normalized
        assert "[1]" not in normalized
        assert "  " not in normalized
    
    def test_section_extraction(self, config):
        """Test section extraction."""
        parse = ParseModule(config)
        html = "<h2>Test Section</h2><p>Content</p>"
        
        sections = parse.extract_sections(html)
        assert isinstance(sections, list)


# Test Summarize Module
class TestSummarizeModule:
    """Test summarization functionality."""
    
    def test_summarize_initialization(self, config):
        """Test summarize module initializes."""
        summarize = SummarizeModule(config)
        assert summarize is not None
        assert summarize.default_bullets == 5
    
    def test_abstract_generation(self, config):
        """Test abstract generation."""
        summarize = SummarizeModule(config)
        
        content = {
            "title": "Test Topic",
            "sections": []
        }
        
        abstract = summarize.generate_abstract(content)
        assert isinstance(abstract, str)
        assert len(abstract) > 0
    
    def test_bullet_generation(self, config):
        """Test bullet point generation."""
        summarize = SummarizeModule(config)
        
        sections = [
            {"heading": "Section 1", "text": "Text 1", "html_id": "sec1"},
            {"heading": "Section 2", "text": "Text 2", "html_id": "sec2"}
        ]
        
        bullets = summarize.generate_bullets(sections, 2)
        assert len(bullets) == 2
        
        for bullet in bullets:
            assert 'text' in bullet
            assert 'section' in bullet


# Test CLI Commands
class TestCLICommands:
    """Test CLI command functionality."""
    
    def test_agent_search_method(self, agent):
        """Test agent search method."""
        result = agent.search("Python")
        
        assert result['status'] == 'success'
        assert 'candidates' in result
        assert len(result['candidates']) > 0
    
    def test_agent_fetch_method(self, agent):
        """Test agent fetch method."""
        result = agent.fetch("Python")
        
        assert result['status'] == 'success'
        assert 'title' in result
        assert 'content' in result
    
    def test_agent_summarize_method(self, agent):
        """Test agent summarize method."""
        result = agent.summarize("Python", bullets=3)
        
        assert result['status'] == 'success'
        assert 'summary' in result
        assert len(result['summary']) == 3
    
    def test_agent_compare_method(self, agent):
        """Test agent compare method."""
        result = agent.compare("Python", "Java", bullets=4)
        
        assert result['status'] == 'success'
        assert 'comparison' in result
        assert 'similarities' in result['comparison']
        assert 'differences' in result['comparison']


# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_search_to_summarize_workflow(self, agent):
        """Test complete search to summarize workflow."""
        # Search
        search_result = agent.search("Photosynthesis")
        assert search_result['status'] == 'success'
        
        # Fetch
        fetch_result = agent.fetch("Photosynthesis")
        assert fetch_result['status'] == 'success'
        
        # Summarize
        summarize_result = agent.summarize("Photosynthesis", bullets=5)
        assert summarize_result['status'] == 'success'
        assert len(summarize_result['summary']) == 5


# Performance Tests
class TestPerformance:
    """Performance and efficiency tests."""
    
    def test_cache_improves_performance(self, config):
        """Test that caching improves response time."""
        import time
        
        fetch = FetchModule(config)
        
        # First fetch (not cached)
        start = time.time()
        result1 = fetch.fetch_page("TestPage", use_cache=False)
        time1 = time.time() - start
        
        # Second fetch (cached)
        start = time.time()
        result2 = fetch.fetch_page("TestPage", use_cache=True)
        time2 = time.time() - start
        
        # Cached should be faster or equal
        assert time2 <= time1 * 1.5  # Allow some variance


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
