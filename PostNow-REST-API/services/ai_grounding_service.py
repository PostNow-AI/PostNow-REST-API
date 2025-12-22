"""
Serviço para processamento de grounding metadata do Gemini AI.

Este serviço é responsável por extrair e estruturar metadados de grounding
(Google Search) retornados pela API do Gemini quando a ferramenta de busca é utilizada.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AiGroundingService:
    """Service for processing Gemini AI grounding metadata."""
    
    @staticmethod
    def extract_metadata(grounding_metadata: Any) -> Optional[Dict[str, Any]]:
        """
        Extract and structure grounding metadata from Gemini response.
        
        Args:
            grounding_metadata: Raw grounding metadata object from Gemini API
            
        Returns:
            Structured dictionary with web_search_queries and grounding_chunks,
            or None if no metadata available
            
        Example:
            >>> metadata = extract_metadata(raw_metadata)
            >>> print(metadata['web_search_queries'])
            ['query1', 'query2']
            >>> print(metadata['grounding_chunks'][0])
            {'uri': 'https://example.com', 'title': 'Example Title'}
        """
        if not grounding_metadata:
            return None
            
        logger.info(f"[GROUNDING_DEBUG] Metadata object received: {type(grounding_metadata)}")
        
        metadata_dict = {
            'web_search_queries': [],
            'grounding_chunks': []
        }
        
        # Extract web search queries
        if hasattr(grounding_metadata, 'web_search_queries') and grounding_metadata.web_search_queries:
            metadata_dict['web_search_queries'] = list(grounding_metadata.web_search_queries)
            logger.info(f"[GROUNDING_DEBUG] Found {len(metadata_dict['web_search_queries'])} search queries")
        
        # Extract grounding chunks with URLs
        if hasattr(grounding_metadata, 'grounding_chunks') and grounding_metadata.grounding_chunks:
            logger.info(f"[GROUNDING_DEBUG] Found {len(grounding_metadata.grounding_chunks)} grounding chunks")
            
            for chunk in grounding_metadata.grounding_chunks:
                chunk_data = AiGroundingService._extract_chunk_data(chunk)
                if chunk_data:
                    metadata_dict['grounding_chunks'].append(chunk_data)
            
            logger.info(f"[GROUNDING_DEBUG] Extracted {len(metadata_dict['grounding_chunks'])} URLs from chunks")
        else:
            logger.warning("[GROUNDING_DEBUG] NO grounding_chunks found in metadata!")
        
        return metadata_dict
    
    @staticmethod
    def _extract_chunk_data(chunk: Any) -> Optional[Dict[str, str]]:
        """
        Extract URI and title from a single grounding chunk.
        
        Args:
            chunk: Single chunk from grounding_chunks
            
        Returns:
            Dictionary with 'uri' and 'title' if available, None otherwise
        """
        chunk_data = {}
        
        # Try to extract from 'web' attribute
        if hasattr(chunk, 'web') and chunk.web:
            if hasattr(chunk.web, 'uri') and chunk.web.uri:
                chunk_data['uri'] = chunk.web.uri
            if hasattr(chunk.web, 'title') and chunk.web.title:
                chunk_data['title'] = chunk.web.title
        
        # Also check 'retrieved_context' which might have different URL format
        elif hasattr(chunk, 'retrieved_context') and chunk.retrieved_context:
            if hasattr(chunk.retrieved_context, 'uri') and chunk.retrieved_context.uri:
                chunk_data['uri'] = chunk.retrieved_context.uri
            if hasattr(chunk.retrieved_context, 'title') and chunk.retrieved_context.title:
                chunk_data['title'] = chunk.retrieved_context.title
        
        # Log chunk structure for debugging if no data was extracted
        if not chunk_data and hasattr(chunk, '__dict__'):
            logger.debug(f"[GROUNDING_DEBUG] Chunk structure: {chunk.__dict__}")
        
        return chunk_data if chunk_data else None
    
    @staticmethod
    def format_sources_for_display(metadata: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format grounding metadata sources for display in UI or emails.
        
        Args:
            metadata: Structured metadata dict from extract_metadata()
            
        Returns:
            List of formatted source dictionaries with 'url' and 'title'
            
        Example:
            >>> sources = format_sources_for_display(metadata)
            >>> for source in sources:
            ...     print(f"{source['title']}: {source['url']}")
        """
        if not metadata or 'grounding_chunks' not in metadata:
            return []
        
        sources = []
        for chunk in metadata['grounding_chunks']:
            if 'uri' in chunk:
                sources.append({
                    'url': chunk['uri'],
                    'title': chunk.get('title', chunk['uri'])
                })
        
        return sources

