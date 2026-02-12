"""
Summarize Module - Content Summarization and Comparison

Handles:
- Bullet point generation
- Abstract generation
- Topic comparison
- Citation attachment to summaries
"""

import logging
import re
from typing import List, Dict, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class SummarizeModule:
    """Content summarization and comparison with NLP-like features."""
    
    def __init__(self, config: dict):
        """Initialize summarize module."""
        self.config = config
        self.default_bullets = config.get("default_summary_bullets", 5)
        logger.info(f"  [OK] SummarizeModule initialized (default bullets={self.default_bullets})")
    
    def generate_abstract(self, content: Dict) -> str:
        """
        Generate a 1-2 sentence abstract from page content using extractive summarization.
        
        Args:
            content: Page content dictionary
        
        Returns:
            Abstract string
        """
        logger.info(f"  [ABSTRACT] Generating for: '{content.get('title', 'Unknown')}'")
        
        extract = content.get('extract', '') or content.get('content', '')
        if not extract:
            abstract = f"Article about {content.get('title', 'the topic')}."
            logger.info(f"  [OK] Abstract generated ({len(abstract)} chars)")
            return abstract
        
        sentences = self._split_sentences(extract)
        if sentences:
            abstract = " ".join(sentences[:2])
        else:
            abstract = extract[:200] + "..."
        
        logger.info(f"  [OK] Abstract generated ({len(abstract)} chars)")
        return abstract
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex.
        """
        text = text.replace('\\n', ' ').replace('\n', ' ')
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def generate_bullets(self, sections: List[Dict], num_bullets: int) -> List[Dict]:
        """
        Generate bullet point summary from sections using extractive summarization.
        
        Args:
            sections: List of page sections
            num_bullets: Number of bullets to generate
        
        Returns:
            List of bullet points with citations
        """
        logger.info(f"  [BULLETS] Generating {num_bullets} point(s)")
        
        if not sections:
            logger.info(f"  [INFO] No sections provided")
            return []
        
        bullets = []
        scored_sections = []
        
        for section in sections:
            text = section.get('text', '')
            if text:
                score = self._score_section(section)
                scored_sections.append((score, section))
        
        scored_sections.sort(key=lambda x: x[0], reverse=True)
        
        for i, (score, section) in enumerate(scored_sections[:num_bullets]):
            heading = section.get('heading', 'Section')
            text = section.get('text', '')
            
            key_sentence = self._extract_key_sentence(text, heading)
            
            bullet = {
                "text": key_sentence if key_sentence else f"Key point from {heading}",
                "section": heading,
                "section_id": section.get('html_id', ''),
                "score": score
            }
            bullets.append(bullet)
        
        logger.info(f"  [OK] Generated {len(bullets)} bullet(s)")
        return bullets
    
    def _score_section(self, section: Dict) -> float:
        """
        Score a section based on content quality.
        """
        text = section.get('text', '')
        heading = section.get('heading', '')
        
        length_score = min(10, len(text.split()) / 20)
        
        words = text.lower().split()
        unique_ratio = len(set(words)) / max(len(words), 1)
        diversity_score = unique_ratio * 10
        
        has_numbers = bool(re.search(r'\d{1,4}', text))
        number_score = 3 if has_numbers else 0
        
        intro_boost = 2 if heading.lower() in ['introduction', 'overview', 'summary'] else 0
        
        return length_score + diversity_score + number_score + intro_boost
    
    def _extract_key_sentence(self, text: str, context: str = "") -> str:
        """
        Extract the most important sentence from text.
        """
        sentences = self._split_sentences(text)
        if not sentences:
            return ""
        
        scored = []
        for sent in sentences:
            words = sent.split()
            if 5 <= len(words) <= 30:
                context_score = 1
                if context.lower() in sent.lower():
                    context_score = 2
                score = len(set(words)) * context_score
                scored.append((score, sent))
        
        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1][:150]
        
        return sentences[0][:150] if sentences else ""
    
    def generate_summary(self, content: Dict, num_bullets: int = None) -> Dict:
        """
        Generate complete summary (abstract + bullets).
        
        Args:
            content: Page content
            num_bullets: Number of bullets (defaults to config)
        
        Returns:
            Summary dictionary
        """
        if num_bullets is None:
            num_bullets = self.default_bullets
        
        logger.info(f"[INFO] Generating full summary ({num_bullets} bullets)")
        
        abstract = self.generate_abstract(content)
        sections = content.get('sections', [])
        bullets = self.generate_bullets(sections, num_bullets)
        
        summary = {
            "title": content.get('title', 'Unknown'),
            "url": content.get('url', ''),
            "abstract": abstract,
            "bullets": bullets,
            "total_points": len(bullets),
            "timestamp": content.get('timestamp', '')
        }
        
        logger.info("[OK] Summary generated")
        return summary
    
    def compare_topics(self, topic1_content: Dict, topic2_content: Dict, num_points: int = 5) -> Dict:
        """
        Compare two Wikipedia topics using keyword analysis.
        
        Args:
            topic1_content: First topic content
            topic2_content: Second topic content
            num_points: Number of comparison points
        
        Returns:
            Comparison dictionary with similarities and differences
        """
        logger.info(f"  [COMPARE] '{topic1_content.get('title')}' vs '{topic2_content.get('title')}'")
        
        text1 = topic1_content.get('extract', '') or topic1_content.get('content', '')
        text2 = topic2_content.get('extract', '') or topic2_content.get('content', '')
        
        keywords1 = self._extract_keywords(text1)
        keywords2 = self._extract_keywords(text2)
        
        common = set(keywords1) & set(keywords2)
        unique1 = set(keywords1) - set(keywords2)
        unique2 = set(keywords2) - set(keywords1)
        
        similarities = [f"Both involve {kw}" for kw in list(common)[:num_points//2]]
        differences = [
            f"{topic1_content.get('title')} relates to {kw}" for kw in list(unique1)[:num_points//2]
        ] + [
            f"{topic2_content.get('title')} relates to {kw}" for kw in list(unique2)[:num_points//2]
        ]
        
        logger.info(f"  [OK] Found {len(similarities)} similarities, {len(differences)} differences")
        
        return {
            "topic1": topic1_content.get('title', 'Topic 1'),
            "topic2": topic2_content.get('title', 'Topic 2'),
            "similarities": similarities,
            "differences": differences
        }
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract top keywords from text using frequency analysis.
        """
        if not text:
            return []
        
        text = text.lower()
        text = re.sub(r'[^a-z\s]', ' ', text)
        words = text.split()
        
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'in', 'on', 'at',
            'to', 'of', 'and', 'or', 'but', 'not', 'what', 'which', 'who',
            'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'such', 'as', 'for', 'from', 'with'
        }
        
        filtered = [w for w in words if len(w) > 3 and w not in stop_words]
        counter = Counter(filtered)
        keywords = [w for w, _ in counter.most_common(top_n)]
        
        return keywords
    
    def extract_glossary(self, content: Dict, num_terms: int = 8) -> List[Dict]:
        """
        Extract key terms and create glossary using keyword extraction.
        
        Args:
            content: Page content
            num_terms: Number of terms to extract
        
        Returns:
            List of glossary entries
        """
        logger.info(f"  [GLOSSARY] Extracting {num_terms} term(s)")
        
        text = content.get('extract', '') or content.get('content', '')
        keywords = self._extract_keywords(text, top_n=num_terms)
        
        glossary = []
        for i, keyword in enumerate(keywords[:num_terms]):
            glossary.append({
                "term": keyword.title(),
                "definition": f"Key concept mentioned in the article",
                "section": "Content",
                "citation": "Main article"
            })
        
        logger.info(f"  [OK] Glossary extracted with {len(glossary)} term(s)")
        return glossary
