import pytest
from unittest.mock import patch, MagicMock
from integration.layback import OperatorAgent

@patch('integration.layback.inject_teams_ui')
@patch('integration.layback.inject_via_playwright')
def test_operator_agent_success(mock_playwright, mock_ui):
    # API funciona
    mock_ui.return_value = True
    
    result = OperatorAgent.inject_teams(123, 'dummy.json')
    
    assert result is True
    mock_ui.assert_called_once()
    mock_playwright.assert_not_called()

@patch('integration.layback.inject_teams_ui')
@patch('integration.layback.inject_via_playwright')
def test_operator_agent_fallback_on_failure(mock_playwright, mock_ui):
    # API retorna False
    mock_ui.return_value = False
    mock_playwright.return_value = True
    
    result = OperatorAgent.inject_teams(123, 'dummy.json')
    
    assert result is True
    mock_ui.assert_called_once()
    mock_playwright.assert_called_once()

@patch('integration.layback.inject_teams_ui')
@patch('integration.layback.inject_via_playwright')
def test_operator_agent_fallback_on_exception(mock_playwright, mock_ui):
    from requests.exceptions import Timeout
    mock_ui.side_effect = Timeout("Timeout na API")
    mock_playwright.return_value = True
    
    result = OperatorAgent.inject_teams(123, 'dummy.json')
    
    assert result is True
    mock_ui.assert_called_once()
    mock_playwright.assert_called_once()
