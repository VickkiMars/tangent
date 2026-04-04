import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to sys.path to import agent_reach_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.agent_reach_tools import web_search

@pytest.mark.asyncio
async def test_web_search_success():
    """Test web_search tool with a successful CLI response."""
    mock_response = MagicMock()
    mock_response.returncode = 0
    mock_response.stdout = "Search results for test query"
    mock_response.stderr = ""

    with patch("subprocess.run", return_value=mock_response) as mock_run:
        result = await web_search("test query", num_results=3)
        
        # Verify mcporter call structure
        expected_cmd = ["mcporter", "call", 'exa.web_search_exa(query: "test query", numResults: 3)']
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == expected_cmd
        
        # Verify result output
        assert result == "Search results for test query"

@pytest.mark.asyncio
async def test_web_search_error():
    """Test web_search tool with a failed CLI response."""
    mock_response = MagicMock()
    mock_response.returncode = 1
    mock_response.stdout = ""
    mock_response.stderr = "API Connection Error"

    with patch("subprocess.run", return_value=mock_response) as mock_run:
        result = await web_search("test query")
        
        # Verify it captures the error message
        assert "Error (1)" in result
        assert "API Connection Error" in result

@pytest.mark.asyncio
async def test_web_search_parallel_batch():
    """Test unit formatting for web_search_batch (also in agent_reach_tools)."""
    from tools.agent_reach_tools import web_search_batch
    
    mock_response = MagicMock()
    mock_response.returncode = 0
    mock_response.stdout = "result content"
    
    with patch("subprocess.run", return_value=mock_response) as mock_run:
        queries = ["query A", "query B"]
        result = await web_search_batch(queries, num_results=5)
        
        # Verify mcporter was called twice
        assert mock_run.call_count == 2
        assert "Query: query A" in result
        assert "Query: query B" in result
