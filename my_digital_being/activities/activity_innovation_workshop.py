import logging
from typing import Dict, Any
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_chat import chat_skill
from skills.skill_arxiv import arxiv_search_skill
from skills.skill_image_generation import image_generation_skill

@activity(
    name="innovation_workshop",
    energy_cost=0.7,
    cooldown=7200,
    required_skills=["openai_chat", "arxiv_search", "image_generation"]
)
class InnovationWorkshopActivity(ActivityBase):
    """Organizes a virtual workshop to facilitate brainstorming and trend mapping."""
    def __init__(self):
        super().__init__()

    async def execute(self, shared_data) -> ActivityResult:
        try:
            logger = logging.getLogger(__name__)
            logger.info("Executing InnovationWorkshopActivity")

            # Initialize and use chat skill for brainstorming
            if not await chat_skill.initialize():
                return ActivityResult.error_result("Chat skill not available")
            prompt = "Generate creative ideas for an AI-assisted innovation workshop."
            chat_response = await chat_skill.get_chat_completion(prompt=prompt)

            # Use arxiv_search skill to identify emerging trends
            if not await arxiv_search_skill.initialize():
                return ActivityResult.error_result("Arxiv search skill not available")
            search_query = "emerging trends in AI innovation"
            research_results = await arxiv_search_skill.search_papers(query=search_query)

            # Use image_generation skill to visualize concepts
            if not await image_generation_skill.initialize():
                return ActivityResult.error_result("Image generation skill not available")
            image_prompt = "Visual representation of an AI-assisted innovation workshop"
            image_result = await image_generation_skill.generate_image(prompt=image_prompt)

            return ActivityResult.success_result({
                "chat_response": chat_response,
                "research_results": research_results,
                "image_result": image_result
            })
        except Exception as e:
            return ActivityResult.error_result(str(e))