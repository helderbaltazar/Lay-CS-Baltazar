import pytest
from unittest.mock import patch, MagicMock
import agents.react_agent

@patch('agents.react_agent.genai')
@patch('agents.react_agent.AVAILABLE_TOOLS')
def test_diagnose_and_heal_success(mock_tools, mock_genai):
    from agents.react_agent import diagnose_and_heal
    # Setup mock Gemini
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"thought": "test", "tool_to_call": "refresh_layback_cookies", "should_retry": true}'
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model
    
    # Setup mock tools
    mock_tool = MagicMock()
    mock_tools.__contains__.return_value = True
    mock_tools.__getitem__.return_value = mock_tool
    
    with patch('os.getenv', return_value="fake_key"):
        result = diagnose_and_heal("injection", "HTTP 401", "traceback here")
    
    assert result is True
    mock_tool.assert_called_once()
