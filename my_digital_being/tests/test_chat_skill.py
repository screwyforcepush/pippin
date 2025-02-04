import asyncio
from skills.skill_chat import chat_skill

async def main():
    # Initialize the chat skill.
    initialized = await chat_skill.initialize()
    if not initialized:
        print("Failed to initialize chat skill.")
        return
    print("Chat skill initialized successfully!")

    # Use a test prompt to get a chat completion.
    prompt = "Tell me one interesting fact about cats."
    response = await chat_skill.get_chat_completion(
        prompt=prompt,
        system_prompt="You are a friendly AI that shares fun facts.",
        max_tokens=50
    )

    # Check and display the response.
    if response.get("success"):
        content = response["data"].get("content", "")
        print("Chat completion response:")
        print(content)
    else:
        error = response.get("error", "Unknown error")
        print("Chat completion failed:")
        print(error)

if __name__ == "__main__":
    asyncio.run(main()) 