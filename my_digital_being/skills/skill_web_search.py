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
        We'll use skill_name = "web_search" and required_api_keys = ["TAVILY"].
        That means the key is stored under "WEB_SEARCH_TAVILY_API_KEY".
        """
        self.skill_name = "web_search"
        self.required_api_keys = ["TAVILY"]
        api_manager.register_required_keys(self.skill_name, self.required_api_keys)

        self._initialized = False
        self._client: Optional[TavilyClient] = None
        self.search_depth: str = "basic"
        self.default_topic: str = "general"
        self.default_max_tokens: int = 8000

    async def initialize(self) -> bool:
        """
        1) Load skill config from being.configs["skills_config"]["web_search"]
        2) Retrieve the user-provided key from secret manager as "TAVILY".
        3) Initialize TavilyClient with the key.
        """
        try:
            # Load the config from the being
            being = DigitalBeing()
            being.initialize()
            skill_cfg = being.configs.get("skills_config", {}).get("web_search", {})

            # Load configuration with defaults
            self.search_depth = skill_cfg.get("search_depth", "basic")
            self.default_topic = skill_cfg.get("default_topic", "general")
            self.default_max_tokens = skill_cfg.get("max_tokens", 8000)
            
            logger.info(f"Web search skill using search_depth={self.search_depth}, default_topic={self.default_topic}")

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
            logger.error(f"Failed to initialize Web search skill: {e}", exc_info=True)
            self._initialized = False
            return False

    async def search(
        self,
        query: str,
        search_depth: Optional[str] = None,
        topic: Optional[str] = None,
        time_range: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Perform a web search using Tavily and return context suitable for RAG applications.

        Args:
            query: The search query
            search_depth: "basic" or "advanced" search depth (defaults to configured value)
            topic: The category of the search (defaults to configured value)
            time_range: Time range filter for the search (e.g., "day", "week", "month", "year")
            max_tokens: Maximum number of tokens to return in the context (defaults to configured value)

        Returns:
            Dictionary containing search context and metadata
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "Web search skill not initialized",
                "data": None,
            }

        try:
            # Use configured defaults if parameters not provided
            search_depth = search_depth or self.search_depth
            topic = topic or self.default_topic
            max_tokens = max_tokens or self.default_max_tokens

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
                    "used_config": {
                        "search_depth": search_depth,
                        "topic": topic,
                        "max_tokens": max_tokens
                    }
                },
                "error": None,
            }

        except Exception as e:
            logger.error(f"Error in Web search: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "data": None,
            }


# Global instance
web_search_skill = WebSearchSkill() 