"""Activity for fetching research papers from arXiv."""

import logging
from typing import Dict, Any, List
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_arxiv import ArxivSkill
from skills.skill_chat import chat_skill
from framework.main import DigitalBeing

logger = logging.getLogger(__name__)


@activity(
    name="fetch_research",
    energy_cost=0.3,
    cooldown=3600,  # 1 hour
    required_skills=["arxiv_search", "openai_chat"],
)
class FetchResearchActivity(ActivityBase):
    def __init__(self):
        super().__init__()
        self.categories = ["cs.AI", "cs.CL", "cs.LG"]  # AI, Comp Ling, Machine Learning
        self.max_papers = 5
        self.default_query = "artificial intelligence OR machine learning OR neural networks"
        self.system_prompt = (
            "You are a research assistant that generates concise academic search queries for arXiv. "
            "Your goal is to transform thoughts and ideas into focused search queries that will "
            "find relevant research papers. Follow these guidelines:"
            "\n1. Keep queries simple and direct (2-3 key terms maximum)"
            "\n2. Use basic Boolean operators sparingly (prefer single OR between alternatives)"
            "\n3. Avoid complex nested expressions"
            "\n4. Focus on the most essential concept from the input"
            "\n5. Use common technical terms rather than highly specific jargon"
            "\nExample good query: 'reinforcement learning OR deep learning'"
            "\nExample bad query: '(neural networks AND optimization) OR (deep learning AND transformers)'"
        )

    async def generate_arxiv_query(self, memory) -> str:
        """Generate an optimized arXiv search query based on recent daily thoughts."""
        try:
            # Initialize chat skill
            if not await chat_skill.initialize():
                logger.error("Failed to initialize chat skill")
                return self.default_query

            # Look for recent daily thoughts
            recent_activities = memory.get_recent_activities(limit=5)
            recent_thought = None
            
            for activity in recent_activities:
                if activity["activity_type"] == "DailyThoughtActivity" and activity["success"]:
                    if "data" in activity and "thought" in activity["data"]:
                        recent_thought = activity["data"]["thought"]
                        break

            if not recent_thought:
                logger.info("No recent daily thoughts found, using default query")
                return self.default_query

            # Generate arXiv query from the thought
            prompt = (
                f"Based on this thought:\n{recent_thought}\n\n"
                "Generate a formal academic search query suitable for arXiv. The query should "
                "help find computer science research papers related to the core concepts in "
                "this thought. Use appropriate Boolean operators and academic terminology."
            )

            result = await chat_skill.get_chat_completion(
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_tokens=100
            )

            if not result["success"]:
                logger.error(f"Failed to generate query: {result['error']}")
                return self.default_query

            query = result["data"]["content"].strip()
            logger.info(f"Generated arXiv query: {query}")
            return query

        except Exception as e:
            logger.error(f"Error generating arXiv query: {e}")
            return self.default_query

    async def execute(self, shared_data) -> ActivityResult:
        """Execute the research paper fetching activity."""
        try:
            logger.info("Starting research paper fetch activity")

            # Initialize the ArXiv skill with configuration
            arxiv_skill = ArxivSkill()

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

            # Generate the arXiv query
            query = await self.generate_arxiv_query(memory)
            
            # Fetch papers for each category
            all_papers = []
            for category in self.categories:
                papers = await arxiv_skill.search_papers(
                    query=query,
                    max_results=self.max_papers,
                    category=category
                )
                all_papers.extend(papers)

            logger.info(f"Successfully fetched {len(all_papers)} papers")
            return ActivityResult(
                success=True,
                data={
                    "type": "research",
                    "papers": all_papers,
                    "count": len(all_papers),
                    "query": query,
                    "timestamp": shared_data.get("timestamp", "")
                },
                metadata={
                    "categories": self.categories,
                    "max_papers_per_category": self.max_papers,
                    "query": query
                },
            )

        except Exception as e:
            logger.error(f"Failed to fetch research papers: {e}")
            return ActivityResult(success=False, error=str(e))


# Global instance
activity = FetchResearchActivity() 