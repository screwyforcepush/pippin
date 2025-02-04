"""
Web Research Activity

This activity allows the AI to perform web research on topics it's interested in
or needs to learn about. It uses the web search skill to gather information.
"""

import logging
from typing import Dict, Any
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_web_search import web_search_skill
from skills.skill_chat import chat_skill
from framework.main import DigitalBeing

logger = logging.getLogger(__name__)


@activity(
    name="web_research",
    energy_cost=0.3,
    cooldown=3600,  # 1 hour
    required_skills=["web_search", "openai_chat"],
)
class WebResearchActivity(ActivityBase):
    """Activity for conducting web research on topics of interest."""

    def __init__(self):
        super().__init__()
        self.default_topic = "latest developments in artificial intelligence"
        self.system_prompt = (
            "You are a research assistant that generates focused web search queries. "
            "Your goal is to transform thoughts and ideas into clear, specific search queries "
            "that will yield relevant and current web results. The queries should be:"
            "\n1. Specific and targeted"
            "\n2. Use relevant keywords"
            "\n3. Focus on recent developments when appropriate"
            "\n4. Avoid overly broad or vague terms"
        )

    async def generate_search_query(self, memory) -> str:
        """Generate an optimized search query based on recent daily thoughts."""
        try:
            # Initialize chat skill
            if not await chat_skill.initialize():
                logger.error("Failed to initialize chat skill")
                return self.default_topic

            # Look for recent daily thoughts
            recent_activities = memory.get_recent_activities(limit=5)
            recent_thought = None
            
            for activity in recent_activities:
                if activity["activity_type"] == "DailyThoughtActivity" and activity["success"]:
                    if "data" in activity and "thought" in activity["data"]:
                        recent_thought = activity["data"]["thought"]
                        break

            if not recent_thought:
                logger.info("No recent daily thoughts found, using default topic")
                return self.default_topic

            # Generate search query from the thought
            prompt = (
                f"Based on this thought:\n{recent_thought}\n\n"
                "Generate a specific, focused web search query that will help explore "
                "the most interesting aspects of this idea. The query should be optimized "
                "for finding current, relevant web content."
            )

            result = await chat_skill.get_chat_completion(
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_tokens=50
            )

            if not result["success"]:
                logger.error(f"Failed to generate query: {result['error']}")
                return self.default_topic

            query = result["data"]["content"].strip()
            logger.info(f"Generated search query: {query}")
            return query

        except Exception as e:
            logger.error(f"Error generating search query: {e}")
            return self.default_topic

    async def execute(self, shared_data) -> ActivityResult:
        """Execute the web research activity."""
        try:
            logger.info("Starting web research activity")

            # Initialize the Web Search skill
            if not await web_search_skill.initialize():
                return ActivityResult(
                    success=False,
                    error="Failed to initialize web search skill"
                )

            # Get memory reference
            system_data = shared_data.get_category_data("system")
            memory = system_data.get("memory_ref")
            
            if not memory:
                # Fallback to a global digital being's memory reference
                being = DigitalBeing()
                being.initialize()
                memory = being.memory
                
                if not memory:
                    return ActivityResult(
                        success=False,
                        error="No memory reference available"
                    )

            # Generate the search query
            query = await self.generate_search_query(memory)
            logger.info(f"Starting web research with query: {query}")

            # Perform the web search
            response = await web_search_skill.search(
                query=query
            )

            if not response["success"]:
                error_msg = f"Failed to gather research data: {response.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return ActivityResult(
                    success=False,
                    error=error_msg
                )

            research_data = {
                "type": "research",
                "topic": query,
                "findings": response["data"]["context"].get("results", []),
                "timestamp": shared_data.get("timestamp", "")
            }

            logger.info(f"Successfully completed web research on: {query}")
            return ActivityResult(
                success=True,
                data=research_data,
                metadata={
                    "topic": query,
                    "search_config": response["data"]["used_config"],
                    "result_count": len(response["data"]["context"].get("results", []))
                }
            )

        except Exception as e:
            logger.error(f"Failed to perform web research: {e}")
            return ActivityResult(success=False, error=str(e))


# Global instance
activity = WebResearchActivity() 