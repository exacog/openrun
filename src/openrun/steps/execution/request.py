"""HTTP Request step - makes HTTP requests to external services."""

from typing import Any, ClassVar, Literal

import httpx
from pydantic import BaseModel, Field

from openrun.core.interpolation import Interpolated
from openrun.core.output import Output
from openrun.core.state import StateContainer
from openrun.core.types import StateType, StepRunStatus, StepType
from openrun.steps.base import Step, StepInfo, StepRunResult


class StepRequestConfig(BaseModel):
    """Configuration for HTTP request step."""

    url: Interpolated[str] = Field(
        description="Request URL",
        json_schema_extra={"placeholder": "https://api.example.com/endpoint"},
    )
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = Field(
        default="GET",
        description="HTTP method",
    )
    headers: dict[str, Interpolated[str]] = Field(
        default_factory=dict,
        description="Request headers",
    )
    body: Interpolated[str] | None = Field(
        default=None,
        description="Request body (JSON)",
        json_schema_extra={
            "ui_widget": "textarea",
            "ui_show_if": {"method": ["POST", "PUT", "PATCH"]},
        },
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )


class StepRequest(Step):
    """Makes HTTP requests to external services.

    Outputs:
    - response: Response body (parsed JSON or text)
    - status_code: HTTP status code
    - response_headers: Response headers as dict

    Ports:
    - success: Fires on 2xx responses
    - error: Fires on 4xx/5xx responses or request failures
    """

    type: StepType = StepType.REQUEST
    config: StepRequestConfig

    _ports: ClassVar[list[str]] = ["success", "error"]

    @classmethod
    def outputs(cls) -> list[Output]:
        return [
            Output(key="response", type=StateType.ANY, description="Response body"),
            Output(
                key="status_code", type=StateType.NUMBER, description="HTTP status code"
            ),
            Output(
                key="response_headers",
                type=StateType.OBJECT,
                description="Response headers",
            ),
        ]

    async def run(
        self, state: StateContainer, config: StepRequestConfig
    ) -> StepRunResult:
        try:
            # Validate URL for SSRF protection
            from openrun.validation.security import validate_safe_url

            validate_safe_url(config.url)

            async with httpx.AsyncClient() as client:
                # Build request kwargs
                kwargs: dict[str, Any] = {
                    "method": config.method,
                    "url": config.url,
                    "headers": config.headers,
                    "timeout": config.timeout,
                }

                # Add body for methods that support it
                if config.body and config.method in ("POST", "PUT", "PATCH"):
                    kwargs["content"] = config.body
                    # Set content-type if not provided
                    if "Content-Type" not in config.headers:
                        kwargs["headers"] = {
                            **config.headers,
                            "Content-Type": "application/json",
                        }

                response = await client.request(**kwargs)

            # Parse response body
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text

            # Update state with response data
            state.set("response", response_body)
            state.set("status_code", response.status_code)
            state.set("response_headers", dict(response.headers))

            # Determine port based on status code
            port = "error" if response.status_code >= 400 else "success"

            return StepRunResult(
                step_id=self.id,
                status=StepRunStatus.SUCCESS,
                fired_ports=[port],
                output_data={
                    "response": response_body,
                    "status_code": response.status_code,
                    "response_headers": dict(response.headers),
                },
            )

        except httpx.TimeoutException:
            return StepRunResult.failure(
                step_id=self.id,
                message="Request timed out",
                code="TIMEOUT",
                fired_ports=["error"],
            )
        except httpx.RequestError as e:
            return StepRunResult.failure(
                step_id=self.id,
                message=f"Request failed: {e}",
                code="REQUEST_ERROR",
                fired_ports=["error"],
            )
        except ValueError as e:
            # SSRF validation error
            return StepRunResult.failure(
                step_id=self.id,
                message=str(e),
                code="INVALID_URL",
                fired_ports=["error"],
            )

    @classmethod
    def info(cls) -> StepInfo:
        return StepInfo(
            name="HTTP Request",
            description="Make HTTP requests to external services",
            icon="http",
            category="integration",
            color="#2196F3",
        )
