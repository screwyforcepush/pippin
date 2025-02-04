"""
Web Research Activity

This activity allows the AI to perform web research on topics it's interested in
or needs to learn about. It uses the Tavily web search skill to gather information
and stores the findings in its memory.
"""

import logging
from typing import Dict, Any, List
from framework.activity import Activity
from skills.skill_web_search import web_search_skill
from skills.skill_chat import chat_skill

logger = logging.getLogger(__name__)


class WebResearchActivity(Activity):
    """Activity for conducting web research on topics of interest."""

    def __init__(self):
        super().__init__(
            name="web_research",
            description="Research topics on the web to expand knowledge and stay updated",
            requires_skills=["web_search"],
        )

    async def _generate_research_queries(self, topic: str) -> List[str]:
        """Generate specific search queries for the given topic."""
        system_prompt = """You are a research assistant helping to break down a topic into specific search queries.
        Generate 3-5 specific, focused search queries that will help gather comprehensive information about the topic.
        Each query should target a different aspect of the topic.
        Format your response as a Python list of strings, one query per line."""

        user_prompt = f"Generate specific search queries to research this topic: {topic}"
        
        response = await chat_skill.get_chat_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=200
        )

        if not response.get("success"):
            logger.error("Failed to generate search queries")
            return [topic]  # Fall back to using the topic directly

        # Extract queries from the response
        try:
            # The response should be in a format like: ["query1", "query2", "query3"]
            queries = eval(response["data"]["content"])
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                return queries
        except Exception as e:
            logger.error(f"Error parsing generated queries: {e}")
        
        return [topic]  # Fall back to using the topic directly

    async def _synthesize_findings(self, topic: str, contexts: List[str]) -> str:
        """Synthesize the search results into a coherent summary."""
        system_prompt = """You are a research assistant tasked with synthesizing information from multiple sources.
        Create a comprehensive but concise summary of the key findings, ensuring to:
        1. Highlight the most important points
        2. Note any conflicting information
        3. Identify areas that might need further research
        Be factual and objective in your synthesis."""

        combined_context = "\n---\n".join(contexts)
        user_prompt = f"Synthesize the following research findings about '{topic}':\n\n{combined_context}"

        response = await chat_skill.get_chat_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=500
        )

        if not response.get("success"):
            logger.error("Failed to synthesize findings")
            return "Failed to synthesize research findings."

        return response["data"]["content"]

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the web research activity.

        The AI will:
        1. Choose a topic to research
        2. Generate specific search queries
        3. Gather information using the web search skill
        4. Synthesize the findings
        5. Store the results in memory
        """
        try:
            # Initialize required skills
            if not await web_search_skill.initialize() or not await chat_skill.initialize():
                return {
                    "success": False,
                    "error": "Failed to initialize required skills",
                }

            # Get the research topic from state or generate one
            topic = state.get("research_topic", "latest developments in artificial intelligence")
            logger.info(f"Starting web research on topic: {topic}")

            # Generate specific search queries
            queries = await self._generate_research_queries(topic)
            logger.info(f"Generated {len(queries)} search queries")

            # Gather information for each query
            contexts = []
            for query in queries:
                response = await web_search_skill.search(
                    query=query,
                    search_depth="advanced",
                    topic="general",
                    time_range="month",
                    max_tokens=4000
                )

                if response.get("success"):
                    context = response["data"]["context"]
                    contexts.append(context)
                else:
                    logger.error(f"Search failed for query: {query}")

            if not contexts:
                return {
                    "success": False,
                    "error": "Failed to gather any research data",
                }

            # Synthesize the findings
            synthesis = await self._synthesize_findings(topic, contexts)

            # Store the results in memory
            memory_entry = {
                "type": "research",
                "topic": topic,
                "queries": queries,
                "synthesis": synthesis,
                "timestamp": state.get("timestamp", ""),
            }

            return {
                "success": True,
                "memory": memory_entry,
                "data": {
                    "topic": topic,
                    "synthesis": synthesis,
                }
            }

        except Exception as e:
            logger.error(f"Error in web research activity: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }


# Global instance
activity = WebResearchActivity() 