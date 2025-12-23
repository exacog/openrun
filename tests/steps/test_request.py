"""Tests for StepRequest."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from openrun.core.state import StateContainer
from openrun.core.types import StepRunStatus
from openrun.steps.execution.request import StepRequest, StepRequestConfig


@pytest.mark.asyncio(loop_scope="session")
class TestStepRequest:
    """Tests for the HTTP request step."""

    async def test_successful_get_request(self):
        """Test successful GET request."""
        step = StepRequest(
            config=StepRequestConfig(
                url="https://api.example.com/data",
                method="GET",
            )
        )
        state = StateContainer()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.headers = {"Content-Type": "application/json"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await step.run(state, step.config)

        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["success"]
        assert state.get("response") == {"result": "success"}
        assert state.get("status_code") == 200

    async def test_error_status_fires_error_port(self):
        """Test that 4xx/5xx responses fire error port."""
        step = StepRequest(
            config=StepRequestConfig(
                url="https://api.example.com/data",
                method="GET",
            )
        )
        state = StateContainer()

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "not found"}
        mock_response.headers = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await step.run(state, step.config)

        assert result.status == StepRunStatus.SUCCESS  # Step succeeded, just error port
        assert result.fired_ports == ["error"]

    async def test_post_request_with_body(self):
        """Test POST request with JSON body."""
        step = StepRequest(
            config=StepRequestConfig(
                url="https://api.example.com/data",
                method="POST",
                body='{"name": "test"}',
            )
        )
        state = StateContainer()

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 123}
        mock_response.headers = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await step.run(state, step.config)

        assert result.status == StepRunStatus.SUCCESS
        assert result.fired_ports == ["success"]

    async def test_timeout_error(self):
        """Test timeout handling."""
        import httpx

        step = StepRequest(
            config=StepRequestConfig(
                url="https://api.example.com/data",
                method="GET",
                timeout=1,
            )
        )
        state = StateContainer()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.request.side_effect = httpx.TimeoutException("timeout")
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await step.run(state, step.config)

        assert result.status == StepRunStatus.ERROR
        assert result.error.code == "TIMEOUT"
        assert result.fired_ports == ["error"]

    async def test_request_error(self):
        """Test request error handling."""
        import httpx

        step = StepRequest(
            config=StepRequestConfig(
                url="https://api.example.com/data",
                method="GET",
            )
        )
        state = StateContainer()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.request.side_effect = httpx.RequestError(
                "connection failed"
            )
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await step.run(state, step.config)

        assert result.status == StepRunStatus.ERROR
        assert result.error.code == "REQUEST_ERROR"

    async def test_text_response(self):
        """Test handling non-JSON response."""
        step = StepRequest(
            config=StepRequestConfig(
                url="https://api.example.com/text",
                method="GET",
            )
        )
        state = StateContainer()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("not JSON")
        mock_response.text = "plain text response"
        mock_response.headers = {"Content-Type": "text/plain"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            result = await step.run(state, step.config)

        assert result.status == StepRunStatus.SUCCESS
        assert state.get("response") == "plain text response"

    def test_outputs_declaration(self):
        """Test that outputs are correctly declared."""
        outputs = StepRequest.outputs()
        keys = [o.key for o in outputs]
        assert "response" in keys
        assert "status_code" in keys
        assert "response_headers" in keys

    def test_info(self):
        """Test step info metadata."""
        info = StepRequest.info()
        assert info.name == "HTTP Request"
        assert info.category == "integration"

    def test_ports(self):
        """Test that request has success and error ports."""
        step = StepRequest(config=StepRequestConfig(url="https://example.com"))
        assert "success" in step.ports
        assert "error" in step.ports
