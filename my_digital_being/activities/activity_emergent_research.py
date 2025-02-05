"""Activity for generating emergent insights by combining research from multiple sources."""

import logging
from typing import Dict, Any, List
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_chat import chat_skill

logger = logging.getLogger(__name__)


@activity(
    name="emergent_research",
    energy_cost=0.5,
    cooldown=200,  # 2 hours
    required_skills=["openai_chat"],
)
class EmergentResearchActivity(ActivityBase):
    """Analyzes research data to generate emergent insights through combinatory play."""

    def __init__(self):
        super().__init__()
        self.system_prompt = """You are an innovative AI researcher skilled at identifying 
        patterns, connections, and novel insights across different research papers and web content. 
        Your goal is to practice combinatory play - connecting seemingly unrelated ideas to generate 
        new insights and hypotheses. Focus on:
        1. Identifying common themes and patterns
        2. Finding unexpected connections between different topics
        3. Generating novel hypotheses and research directions
        4. Highlighting potential breakthroughs or innovative applications
        
        Be specific and concrete in your analysis while maintaining scientific rigor."""

    async def execute(self, shared_data) -> ActivityResult:
        """Execute the emergent research analysis activity."""
        try:
            logger.info("Starting emergent research analysis")

            # Get memory reference using the standard pattern
            system_data = shared_data.get_category_data("system")
            memory = system_data.get("memory_ref")

            if not memory:
                # Fallback to a global digital being's memory reference
                from framework.main import DigitalBeing
                being = DigitalBeing()
                being.initialize()
                memory = being.memory

            # Look for research data in recent activities
            recent_activities = memory.get_recent_activities(limit=20)
            research_data = []

            for activity in recent_activities:
                if activity["success"]:
                    if activity["activity_type"] == "FetchResearchActivity" and "data" in activity:
                        if "papers" in activity["data"]:
                            research_data.extend(activity["data"]["papers"])
                    elif activity["activity_type"] == "WebResearchActivity" and "data" in activity:
                        if "findings" in activity["data"]:
                            research_data.extend(activity["data"]["findings"])

            if not research_data:
                return ActivityResult.error_result("No research data found in recent activities")

            # Initialize chat skill
            if not await chat_skill.initialize():
                return ActivityResult.error_result("Failed to initialize chat skill")

            # Prepare research summary for analysis
            research_summary = self._prepare_research_summary(research_data)

            # Generate emergent insights
            analysis_prompt = f"""Analyze the following research data and generate emergent insights:

            Research Data:
            {research_summary}

            Please provide:
            1. Key patterns and themes identified across sources
            2. Novel connections between different topics
            3. Potential breakthrough ideas or hypotheses
            4. Suggested directions for future research
            """

            result = await chat_skill.get_chat_completion(
                prompt=analysis_prompt,
                system_prompt=self.system_prompt,
                max_tokens=1000,
            )

            if not result["success"]:
                return ActivityResult.error_result(result["error"])

            return ActivityResult.success_result(
                data={
                    "insights": result["data"]["content"],
                    "source_counts": {
                        "research_data": len(research_data)
                    }
                },
                metadata={
                    "model": result["data"]["model"],
                    "finish_reason": result["data"]["finish_reason"],
                }
            )

        except Exception as e:
            logger.error(f"Error in emergent research activity: {e}")
            return ActivityResult.error_result(str(e))

    def _prepare_research_summary(self, research_data: List[Dict]) -> str:
        """Prepare a formatted summary of research data for analysis."""
        summary_parts = []

        for item in research_data:
            summary_parts.append(f"- Title: {item.get('title')}")
            if "summary" in item:  # ArXiv paper
                summary_parts.append(f"  Abstract: {item.get('summary')}")
                summary_parts.append(f"  Categories: {item.get('categories', [])}\n")
            else:  # Web research
                summary_parts.append(f"  Content: {item.get('content')}")
                summary_parts.append(f"  URL: {item.get('url')}\n")

        return "\n".join(summary_parts) 