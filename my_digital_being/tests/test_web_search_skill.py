import asyncio
from skills.skill_web_search import web_search_skill


async def main():
    # Initialize the web search skill
    initialized = await web_search_skill.initialize()
    if not initialized:
        print("Failed to initialize web search skill.")
        return
    print("Web search skill initialized successfully!")

    # Test search context
    search_query = "What are the latest developments in quantum computing?"
    print(f"\nGetting search context for: {search_query}")
    response = await web_search_skill.search(
        query=search_query,
        search_depth="basic",
        topic="general",
        time_range="week",
        max_tokens=2000  # Using a smaller context for testing
    )

    # Check and display the search context
    if response.get("success"):
        data = response["data"]
        print("\nSearch Context:")
        print("-" * 80)
        print(data.get("context"))
        print("-" * 80)
    else:
        error = response.get("error", "Unknown error")
        print("Search failed:")
        print(error)


if __name__ == "__main__":
    asyncio.run(main()) 