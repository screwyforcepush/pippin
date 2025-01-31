"""Activity for fetching news using web scraping."""

import logging
from typing import Dict, Any, List
from framework.activity_decorator import activity, ActivityBase, ActivityResult
from skills.skill_web_scraping import WebScrapingSkill

logger = logging.getLogger(__name__)

# Define news sources for each topic
NEWS_SOURCES = {
    "technology": [
        "https://techcrunch.com",
        "https://www.theverge.com",
    ],
    "science": [
        "https://www.sciencedaily.com",
        "https://www.nature.com/news",
    ],
    "art": [
        "https://news.artnet.com",
        "https://www.artnews.com",
    ]
}

@activity(
    name="fetch_news",
    energy_cost=0.3,
    cooldown=1800,  # 30 minutes
    required_skills=["web_scraping"],
)
class FetchNewsActivity(ActivityBase):
    def __init__(self):
        super().__init__()
        self.topics = ["technology", "science", "art"]
        self.max_articles = 5
        self.web_scraper = WebScrapingSkill()

    async def execute(self, shared_data) -> ActivityResult:
        """Execute the news fetching activity."""
        try:
            logger.info("Starting news fetch activity")

            articles = await self._fetch_articles()

            # Store articles in shared data
            shared_data.set("memory", "latest_news", articles)

            logger.info(f"Successfully fetched {len(articles)} articles")
            return ActivityResult(
                success=True,
                data={"articles": articles, "count": len(articles)},
                metadata={"topics": self.topics, "max_articles": self.max_articles},
            )

        except Exception as e:
            logger.error(f"Failed to fetch news: {e}")
            return ActivityResult(success=False, error=str(e))

    async def _fetch_articles(self) -> List[Dict[str, Any]]:
        """Fetch articles from configured news sources."""
        articles = []
        articles_per_topic = self.max_articles // len(self.topics)

        for topic in self.topics:
            if topic not in NEWS_SOURCES:
                logger.warning(f"No sources configured for topic: {topic}")
                continue

            for source_url in NEWS_SOURCES[topic]:
                if len(articles) >= self.max_articles:
                    break

                try:
                    result = await self.web_scraper.scrape(source_url, parse=True)
                    if not result or not result.get('parsed'):
                        logger.warning(f"Failed to scrape {source_url}")
                        continue

                    # Extract article information from the parsed content
                    parsed = result['parsed']
                    title = parsed.get('title', 'Untitled')
                    summary = parsed.get('body_text', '')[:200] + '...'  # First 200 chars as summary

                    articles.append({
                        'title': title,
                        'topic': topic,
                        'summary': summary,
                        'url': source_url
                    })

                    if len(articles) >= articles_per_topic:
                        break

                except Exception as e:
                    logger.error(f"Error scraping {source_url}: {e}")
                    continue

        return articles
