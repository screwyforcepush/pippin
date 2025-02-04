"""
Tavily-based Web Search Skill that:
 - fetches user-provided key from secret manager
 - passes api_key to TavilyClient
 - provides web search capabilities optimized for RAG
"""

import logging
from typing import Optional, Dict, Any
from tavily import TavilyClient
from framework.api_management import api_manager
from framework.main import DigitalBeing

logger = logging.getLogger(__name__)


class WebSearchSkill:
    """Skill for web search using Tavily with a user-provided key."""

    def __init__(self):
        """
        We'll use skill_name = "tavily" and required_api_keys = ["TAVILY"].
        That means the key is stored under "TAVILY_TAVILY_API_KEY".
        """
        self.skill_name = "tavily"
        self.required_api_keys = ["TAVILY"]
        api_manager.register_required_keys(self.skill_name, self.required_api_keys)

        self._initialized = False
        self._client: Optional[TavilyClient] = None

    async def initialize(self) -> bool:
        """
        1) Retrieve the user-provided key from secret manager as "TAVILY".
        2) Initialize TavilyClient with the key.
        """
        try:
            # Retrieve the user's key from secret manager
            api_key = await api_manager.get_api_key(self.skill_name, "TAVILY")
            if not api_key:
                logger.error("No TAVILY API key found")
                return False

            # Initialize the Tavily client
            self._client = TavilyClient(api_key=api_key)
            logger.info("Successfully initialized Tavily client")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Tavily skill: {e}", exc_info=True)
            self._initialized = False
            return False

    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        topic: str = "general",
        time_range: Optional[str] = None,
        max_tokens: int = 8000,
    ) -> Dict[str, Any]:
        """
        Perform a web search using Tavily and return context suitable for RAG applications.

        Args:
            query: The search query
            search_depth: "basic" or "advanced" search depth
            topic: The category of the search (e.g., "general" or "news")
            time_range: Time range filter for the search (e.g., "day", "week", "month", "year")
            max_tokens: Maximum number of tokens to return in the context (default: 8000)

        Returns:
            Dictionary containing search context and metadata
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "Tavily skill not initialized",
                "data": None,
            }

        try:
            # Get search context optimized for RAG
            context = self._client.get_search_context(
                query=query,
                search_depth=search_depth,
                topic=topic,
                time_range=time_range,
                max_tokens=max_tokens
            )

            return {
                "success": True,
                "data": {
                    "query": query,
                    "context": context,
                },
                "error": None,
            }

        except Exception as e:
            logger.error(f"Error in Tavily search: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None,
            }


# Global instance
web_search_skill = WebSearchSkill() 