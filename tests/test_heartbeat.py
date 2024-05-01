from dotenv import load_dotenv
load_dotenv(dotenv_path='.env.test')
from unittest.mock import patch, MagicMock
import pytest
from heartbeat.heartbeat import Heartbeat


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("ENABLED", "territorytracktask,guildactivitytask")


@pytest.fixture
def mock_tasks():
    with patch('heartbeat.TerritoryTrackTask') as mock_territory:
        with patch('heartbeat.GuildActivityTask') as mock_guild:
            mock_territory.return_value.run = MagicMock(name='run')
            mock_territory.return_value.stop = MagicMock(name='stop')
            mock_guild.return_value.run = MagicMock(name='run')
            mock_guild.return_value.stop = MagicMock(name='stop')
            yield mock_territory.return_value, mock_guild.return_value


@pytest.mark.usefixtures("mock_db")
def test_run_tasks_enabled(mock_env, mock_tasks):
    Heartbeat.run_tasks()
    mock_territory, mock_guild = mock_tasks
    mock_territory.run.assert_called_once()
    mock_guild.run.assert_called_once()


@pytest.mark.usefixtures("mock_db")
def test_stop_tasks_enabled(mock_env, mock_tasks):
    Heartbeat.stop_tasks()
    mock_territory, mock_guild = mock_tasks
    mock_territory.stop.assert_called_once()
    mock_guild.stop.assert_called_once()


@pytest.mark.usefixtures("mock_db")
def test_tasks_not_called_if_disabled(mock_env):
    with patch('heartbeat.PlayerActivityTask') as mock_player:
        mock_player.return_value.run = MagicMock(name='run')
        Heartbeat.run_tasks()
        mock_player.return_value.run.assert_not_called()
