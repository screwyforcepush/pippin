"""
ArXiv Search Skill
Uses arxiv package to search for academic papers on arxiv.org.
No API keys required.
"""

import logging
from typing import List, Dict, Any, Optional
import arxiv
from framework.api_management import api_manager

logger = logging.getLogger(__name__)


class ArxivSkill:
    """
    Skill for searching academic papers on arXiv using the arxiv package.
    No API key required.
    """

    def __init__(self):
        self.skill_name = "arxiv_search"
        self.client = arxiv.Client()
        # Register with api_manager for consistency, though no keys needed
        api_manager.register_required_keys(self.skill_name, [])

    async def search_papers(
        self,
        query: str,
        max_results: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for papers on arXiv based on query and parameters.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            category: Optional arXiv category (e.g., 'cs.AI', 'physics', etc.)

        Returns:
            List of papers with their details
        """
        try:
            # Construct the search query
            full_query = query
            if category:
                full_query = f"cat:{category} AND {query}"

            # Create search object
            search = arxiv.Search(
                query=full_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            # Execute search
            results = list(self.client.results(search))
            
            # Format results
            papers = []
            for paper in results:
                papers.append({
                    "title": paper.title,
                    "authors": [author.name for author in paper.authors],
                    "summary": paper.summary,
                    "published": paper.published.isoformat(),
                    "updated": paper.updated.isoformat(),
                    "doi": paper.doi,
                    "primary_category": paper.primary_category,
                    "categories": paper.categories,
                    "links": [link.href for link in paper.links],
                    "pdf_url": paper.pdf_url,
                })

            logger.info(f"Successfully found {len(papers)} papers matching query: {query}")
            return papers

        except Exception as e:
            logger.error(f"Error searching arXiv: {e}", exc_info=True)
            return [] 
        