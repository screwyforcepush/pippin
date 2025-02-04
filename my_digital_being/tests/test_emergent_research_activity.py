"""Tests for the emergent research activity."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from activities.activity_emergent_research import EmergentResearchActivity
from framework.activity_decorator import ActivityResult


@pytest.fixture
def mock_memory():
    memory = Mock()
    memory.retrieve_data.side_effect = lambda key: {
        "latest_research": [
            {
                "title": "Test Paper 1",
                "summary": "A study on AI",
                "categories": ["cs.AI"]
            }
        ],
        "web_research": [
            {
                "title": "Web Article 1",
                "content": "Recent developments in AI",
                "url": "https://example.com/article1"
            }
        ]
    }.get(key, [])
    return memory


@pytest.fixture
def mock_shared_data(mock_memory):
    shared_data = Mock()
    shared_data.get_category_data.return_value = {"memory_ref": mock_memory}
    shared_data.get_current_time.return_value = datetime.now()
    return shared_data


@pytest.mark.asyncio
async def test_emergent_research_success(mock_shared_data, mock_memory):
    # Mock successful chat completion
    mock_chat_result = {
        "success": True,
        "data": {
            "content": "Test insight content",
            "model": "gpt-4",
            "finish_reason": "stop"
        }
    }

    with patch("activities.activity_emergent_research.chat_skill") as mock_chat_skill:
        mock_chat_skill.initialize.return_value = True
        mock_chat_skill.get_chat_completion.return_value = mock_chat_result

        activity = EmergentResearchActivity()
        result = await activity.execute(mock_shared_data)

        assert result.success is True
        assert "insights" in result.data
        assert result.data["insights"] == "Test insight content"
        assert result.data["source_counts"]["arxiv_papers"] == 1
        assert result.data["source_counts"]["web_sources"] == 1
        
        # Verify memory interactions
        mock_memory.store_data.assert_called_once()


@pytest.mark.asyncio
async def test_emergent_research_no_data(mock_shared_data, mock_memory):
    # Mock empty research data
    mock_memory.retrieve_data.return_value = []

    activity = EmergentResearchActivity()
    result = await activity.execute(mock_shared_data)

    assert result.success is False
    assert "No research data found in memory" in result.error


@pytest.mark.asyncio
async def test_emergent_research_chat_failure(mock_shared_data, mock_memory):
    # Mock failed chat completion
    mock_chat_result = {
        "success": False,
        "error": "Chat API error"
    }

    with patch("activities.activity_emergent_research.chat_skill") as mock_chat_skill:
        mock_chat_skill.initialize.return_value = True
        mock_chat_skill.get_chat_completion.return_value = mock_chat_result

        activity = EmergentResearchActivity()
        result = await activity.execute(mock_shared_data)

        assert result.success is False
        assert "Chat API error" in result.error


@pytest.mark.asyncio
async def test_prepare_research_summary():
    activity = EmergentResearchActivity()
    
    arxiv_papers = [
        {
            "title": "Test Paper",
            "summary": "Test summary",
            "categories": ["cs.AI"]
        }
    ]
    
    web_research = [
        {
            "title": "Web Article",
            "content": "Test content",
            "url": "https://example.com"
        }
    ]

    summary = activity._prepare_research_summary(arxiv_papers, web_research)
    
    assert "ArXiv Papers:" in summary
    assert "Test Paper" in summary
    assert "Web Research:" in summary
    assert "Web Article" in summary 