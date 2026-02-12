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
from typing import Any, Dict, List, Optional
from collections import Counter
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


Section = Dict[str, Any]
Summary = Dict[str, Any]


class SummarizeModule:
    """Content summarization and comparison with NLP-like features."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize summarize module."""
        self.config = config
        self.default_bullets = config.get("default_summary_bullets", 5)
        logger.info(f"  [OK] SummarizeModule initialized (default bullets={self.default_bullets})")
    
    def _clean_html_text(self, text: str) -> str:
        """
        Clean HTML tags from text while preserving content.
        """
        if not text:
            return ""
        
        try:
            soup = BeautifulSoup(text, 'html.parser')
            clean_text = soup.get_text(separator=' ', strip=True)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            clean_text = re.sub(r'\[.*?\]', '', clean_text)  # Remove [citations]
            return clean_text
        except:
            return text
    
    def generate_abstract(self, content: Dict[str, Any]) -> str:
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
    
    def generate_bullets(self, sections: List[Section], num_bullets: int) -> List[Section]:
        """
        Generate bullet point summary from sections using extractive summarization.
        Prioritizes informative content and avoids sparse/generic bullets.
        
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
        
        # Extract key sentences first
        section_bullets = []
        for i, (score, section) in enumerate(scored_sections):
            heading = section.get('heading', 'Section')
            text = section.get('text', '')
            
            key_sentence = self._extract_key_sentence(text, heading)
            
            # Quality check: reject generic or empty bullets
            if key_sentence and not self._is_generic_bullet(key_sentence):
                bullet = {
                    "text": key_sentence,
                    "section": heading,
                    "section_id": section.get('html_id', ''),
                    "score": score,
                    "quality": "high"
                }
                section_bullets.append(bullet)
                
                if len(section_bullets) >= num_bullets:
                    break
        
        # If we have enough high-quality bullets, use them
        if len(section_bullets) >= num_bullets:
            bullets = section_bullets[:num_bullets]
        else:
            # Fallback: use section headings as bullets for remaining slots
            remaining = num_bullets - len(section_bullets)
            bullets = section_bullets
            
            for i, (score, section) in enumerate(scored_sections[len(section_bullets):]):
                if len(bullets) >= num_bullets:
                    break
                
                heading = section.get('heading', 'Section')
                if heading.lower() not in ['references', 'see also', 'notes', 'external links']:
                    text = section.get('text', '')[:100]
                    bullet = {
                        "text": f"{heading}: {text}",
                        "section": heading,
                        "section_id": section.get('html_id', ''),
                        "score": score,
                        "quality": "medium"
                    }
                    bullets.append(bullet)
        
        logger.info(f"  [OK] Generated {len(bullets)} bullet(s)")
        return bullets
    
    def _is_generic_bullet(self, text: str) -> bool:
        """
        Check if bullet text is too generic or placeholder-like.
        """
        generic_patterns = [
            r'^key point', r'^relates to', r'^involves',
            r'^mentioned in', r'^also known as',
            r'^more information', r'^further details'
        ]
        
        text_lower = text.lower()
        return any(re.match(pattern, text_lower) for pattern in generic_patterns)
    
    def _score_section(self, section: Section) -> float:
        """
        Score a section based on content quality and informativeness.
        Prioritizes specific, fact-rich content over generic introductions.
        """
        text = section.get('text', '')
        heading = section.get('heading', '')
        
        # Skip low-value sections
        skip_headings = {'references', 'see also', 'notes', 'external links', 'gallery', 'infobox'}
        if heading.lower() in skip_headings:
            return -100
        
        # Base length score (prefer meaty paragraphs)
        word_count = len(text.split())
        length_score = min(15, word_count / 15)
        
        # Diversity score (varied vocabulary = better content)
        words = text.lower().split()
        unique_ratio = len(set(words)) / max(len(words), 1)
        diversity_score = unique_ratio * 12
        
        # Fact indicators (numbers, dates, names = specific content)
        has_numbers = bool(re.search(r'\d{1,4}', text))
        number_score = 5 if has_numbers else 0
        
        has_years = bool(re.search(r'\b(19|20)\d{2}\b', text))
        year_score = 4 if has_years else 0
        
        # Content quality markers
        content_keywords = {
            'developed': 2, 'created': 2, 'discovered': 2, 'founded': 2,
            'invented': 3, 'pioneered': 3, 'revolutionized': 3,
            'major': 1, 'important': 1, 'significant': 2, 'critical': 2,
            'however': 1, 'unlike': 2, 'difference': 2, 'distinction': 2
        }
        
        content_score = sum(
            count for keyword, count in content_keywords.items() 
            if keyword in text.lower()
        )
        
        # Section-type bonuses
        intro_boost = 0
        if heading.lower() in ['introduction', 'overview', 'background', 'history']:
            intro_boost = 3
        
        career_boost = 0
        if heading.lower() in ['early life', 'career', 'works', 'achievements', 'legacy']:
            career_boost = 2
        
        # Calculate total score
        total_score = (
            length_score + 
            diversity_score + 
            number_score + 
            year_score + 
            content_score + 
            intro_boost + 
            career_boost
        )
        
        return total_score
    
    def _extract_key_sentence(self, text: str, context: str = "") -> str:
        """
        Extract the most important sentence from text using content analysis.
        Prefers sentences with facts, numbers, or specific keywords.
        Cleans HTML tags from result.
        """
        # Clean HTML first
        text = self._clean_html_text(text)
        
        sentences = self._split_sentences(text)
        if not sentences:
            return ""
        
        # Generic patterns to avoid
        generic_starters = {
            "key point", "main idea", "important", "also", "further",
            "however", "therefore", "moreover", "likewise", "additionally"
        }
        
        scored: List[tuple[float, str]] = []
        for sent in sentences:
            sent_lower = sent.lower()
            words = sent.split()
            
            # Skip sentences that are too short or too long
            if not (5 <= len(words) <= 30):
                continue
            
            # Skip generic sentences
            if any(sent_lower.startswith(starter) for starter in generic_starters):
                continue
            
            score: float = 0.0
            
            # Boost score based on sentence quality
            unique_words = len(set(words))
            score += unique_words * 0.5  # Diversity bonus
            
            # Content quality indicators
            has_number = bool(re.search(r'\d+', sent))
            score += 3 if has_number else 0  # Numbers indicate facts
            
            has_verb = bool(re.search(r'\b(is|are|was|were|be|have|has|do|does|created|developed|discovered|established|founded)\b', sent_lower))
            score += 2 if has_verb else 0  # Action verbs indicate substance
            
            has_comparison = bool(re.search(r'\b(first|largest|smallest|most|least|unlike|similar|between)\b', sent_lower))
            score += 2 if has_comparison else 0  # Comparisons are informative
            
            # Context matching bonus
            if context.lower() in sent_lower:
                score += 5
            
            # Penalize overly generic descriptions
            generic_phrases = {"key point", "relates to", "involves", "mentioned in"}
            if any(phrase in sent_lower for phrase in generic_phrases):
                score -= 10
            
            scored.append((score, sent))
        
        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            best_sent = scored[0][1]
            # Limit to reasonable length
            if len(best_sent) > 150:
                best_sent = best_sent[:150].rsplit(' ', 1)[0] + "..."
            return best_sent
        
        # Fallback: use first substantial sentence
        for sent in sentences:
            if len(sent) > 20 and len(sent.split()) >= 5:
                if len(sent) > 150:
                    sent = sent[:150].rsplit(' ', 1)[0] + "..."
                return sent
        
        return sentences[0][:150] if sentences else ""
    
    def generate_summary(self, content: Dict[str, Any], num_bullets: Optional[int] = None) -> Summary:
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
    
    def compare_topics(
        self,
        topic1_content: Dict[str, Any],
        topic2_content: Dict[str, Any],
        num_points: int = 5,
    ) -> Dict[str, Any]:
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
        Extract top keywords from text using frequency analysis and content quality.
        Prioritizes meaningful nouns and descriptors over common words.
        """
        if not text:
            return []
        
        text = text.lower()
        text = re.sub(r'[^a-z\s]', ' ', text)
        words = text.split()
        
        # Comprehensive stop word list
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'in', 'on', 'at',
            'to', 'of', 'and', 'or', 'but', 'not', 'what', 'which', 'who',
            'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'such', 'as', 'for', 'from', 'with',
            'by', 'that', 'this', 'if', 'no', 'yes', 'it', 'its', 'can',
            'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'shall', 'will', 'shall', 'during', 'before', 'after', 'also'
        }
        
        # Filter words: length > 3, not in stop words, not numeric
        filtered = [
            w for w in words 
            if len(w) > 3 and w not in stop_words and not w.isdigit()
        ]
        
        # Boost scoring for meaningful content
        keyword_weights: Dict[str, float] = {}
        for word in filtered:
            # Boost nouns (words ending in -tion, -ment, -ness, -ism, -ity)
            if any(word.endswith(suffix) for suffix in ['tion', 'ment', 'ness', 'ism', 'ity', 'ble']):
                keyword_weights[word] = keyword_weights.get(word, 0) + 1.5
            else:
                keyword_weights[word] = keyword_weights.get(word, 0) + 1.0
        
        # Sort by weighted frequency
        sorted_keywords = sorted(
            keyword_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        keywords = [w for w, _ in sorted_keywords[:top_n]]
        return keywords
    
    def extract_glossary(self, content: Dict[str, Any], num_terms: int = 8) -> List[Dict[str, str]]:
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
        
        glossary: List[Dict[str, str]] = []
        for i, keyword in enumerate(keywords[:num_terms]):
            glossary.append({
                "term": keyword.title(),
                "definition": f"Key concept mentioned in the article",
                "section": "Content",
                "citation": "Main article"
            })
        
        logger.info(f"  [OK] Glossary extracted with {len(glossary)} term(s)")
        return glossary
