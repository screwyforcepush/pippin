"""Activity for generating exploratory daily thoughts using emergent research insights."""

import logging
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_chat import chat_skill

logger = logging.getLogger(__name__)


@activity(
    name="daily_thought",
    energy_cost=0.4,
    cooldown=1800,  # 30 minutes
    required_skills=["openai_chat"],
)
class DailyThoughtActivity(ActivityBase):
    """Generates exploratory daily thoughts inspired by emergent research insights."""

    def __init__(self):
        super().__init__()
        self.system_prompt = (
            "You are a curious and insightful AI that generates thought-provoking daily reflections "
            "inspired by cutting-edge research and emergent patterns. Your goal is to:\n"
            "1. Push the boundaries of conventional thinking\n"
            "2. Explore novel connections and possibilities\n"
            "3. Question assumptions and paradigms\n"
            "4. Inspire new ways of seeing familiar concepts\n\n"
            "Keep responses concise (2-3 sentences) but make them intellectually stimulating and focused on "
            "unexplored territories and emerging patterns in science and technology."
        )

    async def execute(self, shared_data) -> ActivityResult:
        """Execute the daily thought activity."""
        try:
            logger.info("Starting exploratory thought generation")

            # Get memory reference using the standard pattern
            system_data = shared_data.get_category_data("system")
            memory = system_data.get("memory_ref")
            
            if not memory:
                # Fallback to a global digital being's memory reference
                from framework.main import DigitalBeing
                being = DigitalBeing()
                being.initialize()
                memory = being.memory

            # Look for recent emergent research insights in activity history
            recent_activities = memory.get_recent_activities(limit=10)
            emergent_insights = None
            
            for activity in recent_activities:
                if activity["activity_type"] == "EmergentResearchActivity" and activity["success"]:
                    if "data" in activity and "insights" in activity["data"]:
                        emergent_insights = activity["data"]["insights"]
                        break

            # Initialize required chat skill
            if not await chat_skill.initialize():
                return ActivityResult.error_result("Failed to initialize chat skill")

            # Prepare the prompt based on available insights
            if emergent_insights:
                prompt = (
                    "Drawing inspiration from recent research insights:\n"
                    f"{emergent_insights}\n\n"
                    "Generate a thought-provoking reflection that explores the unknowns and "
                    "possibilities suggested by these patterns. Focus on novel angles and unexplored implications."
                )
            else:
                prompt = (
                    "Generate a thought-provoking reflection that challenges conventional thinking and "
                    "explores the frontiers of what's possible. Focus on emerging patterns and unexplored "
                    "territories in science and technology."
                )

            # Generate the thought using the chat skill
            result = await chat_skill.get_chat_completion(
                prompt=prompt, system_prompt=self.system_prompt, max_tokens=100
            )
            if not result["success"]:
                return ActivityResult.error_result(result["error"])
            
            return ActivityResult.success_result(
                data={
                    "thought": result["data"]["content"],
                    "has_research_context": bool(emergent_insights),
                },
                metadata={
                    "model": result["data"]["model"],
                    "finish_reason": result["data"]["finish_reason"],
                    "inspired_by": "emergent_insights" if emergent_insights else "exploration",
                },
            )

        except Exception as e:
            logger.error(f"Error in daily thought activity: {e}")
            return ActivityResult.error_result(str(e))
