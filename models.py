from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ActiveProvidersResponse(BaseModel):
    Providers: list[str] = Field(
        ..., description="The string values for the currently available providers"
    )


class ChatCompletionResponse(BaseModel):
    response: dict[str, Any]


class ChatCompletionRequest(BaseModel):
    model: str = Field(
        ...,
        description="Model identifier (e.g., 'google:gemini-xx' or 'openai:gpt-4')"
    )
    messages: list[dict[str, Any]] = Field(
        ...,
        description="List of message objects in the chat completion format, e.g., [{'role': 'user', 'content': "
                    "'Hello!'}]"
    )
    kwargs: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional optional parameters for provider completion.",
    )
