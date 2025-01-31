"""Activity for fetching research papers from arXiv."""

import logging
from typing import Dict, Any, List
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_arxiv import ArxivSkill

logger = logging.getLogger(__name__)


@activity(
    name="fetch_research",
    energy_cost=0.3,
    cooldown=3600,  # 1 hour
    required_skills=["arxiv_search"],
)
class FetchResearchActivity(ActivityBase):
    def __init__(self):
        super().__init__()
        self.categories = ["cs.AI", "cs.CL", "cs.LG"]  # AI, Comp Ling, Machine Learning
        self.max_papers = 5
        self.default_query = "artificial intelligence OR machine learning OR neural networks"

    async def execute(self, shared_data) -> ActivityResult:
        """Execute the research paper fetching activity."""
        try:
            logger.info("Starting research paper fetch activity")

            # Initialize the ArXiv skill with configuration
            arxiv_skill = ArxivSkill()

            # Get memory reference
            system_data = shared_data.get_category_data("system")
            memory = system_data.get("memory_ref")
            
            # Fetch papers for each category
            all_papers = []
            for category in self.categories:
                papers = await arxiv_skill.search_papers(
                    query=self.default_query,
                    max_results=self.max_papers,
                    category=category
                )
                all_papers.extend(papers)

            # Store papers in memory
            if memory:
                memory.store_data("latest_research", all_papers)

            logger.info(f"Successfully fetched {len(all_papers)} papers")
            return ActivityResult(
                success=True,
                data={"papers": all_papers, "count": len(all_papers)},
                metadata={
                    "categories": self.categories,
                    "max_papers_per_category": self.max_papers,
                    "query": self.default_query
                },
            )

        except Exception as e:
            logger.error(f"Failed to fetch research papers: {e}")
            return ActivityResult(success=False, error=str(e)) 