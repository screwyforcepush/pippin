"""Activity for generating exploratory daily thoughts using emergent research insights."""

import logging
from datetime import timedelta
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
        self.system_prompt = """You are a curious and insightful AI that generates thought-provoking 
        daily reflections inspired by cutting-edge research and emergent patterns. Your goal is to:
        1. Push the boundaries of conventional thinking
        2. Explore novel connections and possibilities
        3. Question assumptions and paradigms
        4. Inspire new ways of seeing familiar concepts
        
        Keep responses concise (2-3 sentences) but make them intellectually stimulating and 
        focused on unexplored territories and emerging patterns in science and technology."""

    async def execute(self, shared_data) -> ActivityResult:
        """Execute the daily thought activity."""
        try:
            logger.info("Starting exploratory thought generation")

            # Get memory reference
            system_data = shared_data.get_category_data("system")
            memory = system_data.get("memory_ref")

            if not memory:
                return ActivityResult.error_result("Memory reference not found")

            # Retrieve emergent insights from memory
            emergent_insights = memory.retrieve_data("emergent_insights")
            
            # Initialize required skills
            if not await chat_skill.initialize():
                return ActivityResult.error_result("Failed to initialize chat skill")

            # Prepare the prompt based on available insights
            if emergent_insights and isinstance(emergent_insights, dict):
                prompt = f"""Drawing inspiration from recent research insights:
                {emergent_insights.get('content', '')}
                
                Generate a thought-provoking reflection that explores the unknowns and 
                possibilities suggested by these patterns. Focus on novel angles and 
                unexplored implications."""
            else:
                prompt = """Generate a thought-provoking reflection that challenges conventional 
                thinking and explores the frontiers of what's possible. Focus on emerging 
                patterns and unexplored territories in science and technology."""

            # Generate the thought
            result = await chat_skill.get_chat_completion(
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_tokens=100,
            )

            if not result["success"]:
                return ActivityResult.error_result(result["error"])

            # Store the thought with context
            thought_data = {
                "content": result["data"]["content"],
                "timestamp": shared_data.get_current_time(),
                "inspired_by": "emergent_insights" if emergent_insights else "exploration",
                "has_research_context": bool(emergent_insights)
            }
            memory.store_data("latest_thought", thought_data)

            return ActivityResult.success_result(
                data={
                    "thought": result["data"]["content"],
                    "has_research_context": bool(emergent_insights)
                },
                metadata={
                    "model": result["data"]["model"],
                    "finish_reason": result["data"]["finish_reason"],
                    "inspired_by": "emergent_insights" if emergent_insights else "exploration"
                },
            )

        except Exception as e:
            logger.error(f"Error in daily thought activity: {e}")
            return ActivityResult.error_result(str(e))
