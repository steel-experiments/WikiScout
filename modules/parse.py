"""
Parse Module - Content Extraction and Normalization

Handles:
- Section extraction and identification
- Infobox parsing
- Text normalization
- Citation detection
"""

import logging
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ParseModule:
    """Wikipedia content parsing functionality with BeautifulSoup4."""
    
    def __init__(self, config: dict):
        """Initialize parse module."""
        self.config = config
        logger.info(f"  [OK] ParseModule initialized")
    
    def clean_html_text(self, text: str) -> str:
        """
        Clean HTML tags from text while preserving content.
        
        Args:
            text: Text that may contain HTML tags
        
        Returns:
            Clean text without HTML tags
        """
        if not text:
            return ""
        
        try:
            # Use BeautifulSoup to extract clean text
            soup = BeautifulSoup(text, 'html.parser')
            clean_text = soup.get_text(separator=' ', strip=True)
            
            # Remove extra whitespace
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            
            # Remove common Wikipedia artifacts
            clean_text = re.sub(r'\[.*?\]', '', clean_text)  # Remove [citations]
            clean_text = re.sub(r'[edit]', '', clean_text)     # Remove [edit] markers
            
            return clean_text
        except Exception as e:
            logger.warning(f"  [WARN] HTML cleaning error: {str(e)}")
            return text
    
    
    def extract_sections(self, html_content: str) -> List[Dict]:
        """
        Extract sections from Wikipedia HTML content using BeautifulSoup.
        Properly cleans HTML tags from all extracted text.
        
        Args:
            html_content: Raw HTML from Wikipedia
        
        Returns:
            List of sections with clean headings and text
        """
        logger.info(f"  [PARSE] Extracting sections from HTML ({len(html_content)} chars)")
        
        if not html_content:
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            sections = []
            current_section = None
            
            # Find all headings and paragraphs
            for element in soup.find_all(['h2', 'h3', 'h4', 'p']):
                if element.name in ['h2', 'h3', 'h4']:
                    level = int(element.name[1])
                    # Get clean text from heading
                    text = element.get_text(strip=True)
                    
                    if '[edit]' in text:
                        text = text.replace('[edit]', '').strip()
                    
                    heading_id = element.get('id', '') or text.lower().replace(' ', '_')
                    
                    if text and text != 'Contents':
                        current_section = {
                            "level": level,
                            "heading": text,
                            "text": "",
                            "html_id": heading_id,
                            "paragraphs": []
                        }
                        sections.append(current_section)
                        
                elif element.name == 'p' and current_section is not None:
                    # Extract clean text from paragraph
                    para_text = element.get_text(strip=True)
                    if para_text:
                        current_section["paragraphs"].append(para_text)
                        if not current_section["text"]:
                            current_section["text"] = para_text[:200]
            
            # Combine paragraphs into full text and clean
            for section in sections:
                full_text = " ".join(section.get("paragraphs", []))
                # Clean any remaining HTML artifacts
                section["text"] = self.clean_html_text(full_text)[:500]
            
            logger.info(f"  [OK] Extracted {len(sections)} section(s)")
            return sections
        
        except Exception as e:
            logger.warning(f"  [WARN] Section extraction error: {str(e)}")
            return []
    
    def parse_html_content(self, html_content: str) -> Dict:
        """
        Parse complete HTML content structure.
        
        Args:
            html_content: Raw HTML
        
        Returns:
            Dictionary with parsed content
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
            
            links = []
            for a in soup.find_all('a'):
                href = a.get('href', '')
                text = a.get_text(strip=True)
                if href and text and not href.startswith('#'):
                    links.append({"text": text, "url": href})
            
            return {
                "paragraphs": paragraphs,
                "links": links,
                "text": " ".join(paragraphs[:5])
            }
        except:
            return {"paragraphs": [], "links": [], "text": ""}
    
    def extract_infobox(self, html_content: str) -> Dict:
        """
        Extract infobox data from Wikipedia page using BeautifulSoup.
        
        Args:
            html_content: Raw HTML from Wikipedia
        
        Returns:
            Dictionary of infobox fields and values
        """
        logger.info(f"  [INFOBOX] Extracting structured data")
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            infobox_data = {"type": "Unknown", "fields": {}}
            
            infobox_table = soup.find('table', {'class': 'infobox'})
            if not infobox_table:
                logger.info(f"  [INFO] No infobox found")
                return infobox_data
            
            rows = infobox_table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if label and value:
                        infobox_data["fields"][label] = value
            
            logger.info(f"  [OK] Infobox extracted with {len(infobox_data['fields'])} field(s)")
            return infobox_data
        
        except Exception as e:
            logger.warning(f"  [WARN] Infobox extraction error: {str(e)}")
            return {"type": "Unknown", "fields": {}}
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize Wikipedia text (remove HTML, normalize whitespace).
        
        Args:
            text: Raw Wikipedia text
        
        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove citation markers [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove Wikipedia markup
        text = text.replace("'''", "").replace("''", "")
        
        return text
    
    def extract_citations(self, text: str) -> List[Dict]:
        """
        Extract and identify citations in text.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of citation references
        """
        # TODO: Parse citation templates
        
        citations = [
            {
                "marker": "[1]",
                "text": "Example citation",
                "url": "https://example.com"
            }
        ]
        
        return citations
    
    def detect_dispute_tags(self, html_content: str) -> List[str]:
        """
        Detect and extract dispute/citation needed tags.
        
        Args:
            html_content: Raw HTML
        
        Returns:
            List of dispute tags found
        """
        # TODO: Implement detection of {{citation needed}}, {{disputed}}, etc.
        
        tags = []
        
        if "citation needed" in html_content.lower():
            tags.append("citation_needed")
        
        if "disputed" in html_content.lower():
            tags.append("disputed")
        
        if len(tags) > 0:
            logger.warning(f"[WARN] Dispute tags detected: {tags}")
        
        return tags
    
    def extract_links(self, content: str) -> List[Dict]:
        """
        Extract Wikipedia internal links.
        
        Args:
            content: Page content
        
        Returns:
            List of internal links
        """
        # TODO: Parse internal links [[link]]
        
        links = [
            {
                "text": "Related Topic",
                "target": "Related_Topic",
                "url": "https://en.wikipedia.org/wiki/Related_Topic"
            }
        ]
        
        return links
