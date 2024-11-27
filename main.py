from pathlib import Path
from urllib.request import Request
from logging import Logger

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import Response
from models import *

from aisuite import Client
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI implementing 'aisuite'",
    description=(
        "This API provides endpoints for generating chat completions using various providers provided in the aisuite "
        "package, fetching available providers, and managing configurations. Built with FastAPI."
    ),
    version="0.1.0",
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
)


def get_logger() -> Logger:
    return logging.getLogger(__file__)  # manage loglevel via env vars?


# Dependency initialization
def get_client(logger: Logger = Depends(get_logger)) -> Client:
    """
    Dependency method to get the Client instance.
    """

    config_path = Path("config.json")

    if not config_path.exists():
        raise ValueError("Config file is missing")

    try:
        # Only load, no further checking assuming the client handles config issues
        with config_path.open("r", encoding="utf-8") as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError during loading of the config file -> {e}")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error while calling {get_client.__name__}. Details: {e}",
            exc_info=True
        )
        raise
    else:
        # If no exceptions occurred, we return the client
        return Client(provider_configs=config_data)


@app.get("/health")
async def health() -> Response:
    logging.debug("Healthcheck called")
    return Response(content="healthy", media_type="text/plain")


@app.post(
    path="/completions",
    response_model=ChatCompletionResponse,
    responses={
        200: {"description": "Chat completion generated successfully."},
        400: {"description": "Bad request. Model not found or invalid input."},
        500: {"description": "Internal server error. Check logs for more details."},
    },
    summary="Generate Chat Completions",
    description=(
            "Given a conversation history and a specified model, this endpoint generates a chat "
            "completion by invoking the appropriate provider"
    ),
)
async def chat_completions(
        request: ChatCompletionRequest,
        client: Client = Depends(get_client),
        logger: Logger = Depends(get_logger)
) -> Response:
    try:

        if request.model not in client.provider_configs:
            logger.info(f"No model found for {request.model}")
            return Response(
                status_code=400,
                content=f"No model found with name {request.model}, please check the providers route to find out what "
                        f"models are available")

        result = client.chat.completions.create(
            model=request.model,
            messages=request.messages,
            **request.kwargs
        )
        return ChatCompletionResponse(response=result)

    except ValueError as e:
        logger.error(
            f"The following error occurred when calling {chat_completions.__name__} : {e}",
            exc_info=True
        )
    except Exception as e:
        logger.error(
            f"Unexpected error while calling {chat_completions.__name__}. Details: {e}",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get(
    path="/providers",
    response_model=ActiveProvidersResponse,
    summary="Returns the active providers",
    description="Retrieve the list of providers that have been configured and are currently active. \nEach provider "
                "represents a source, e.g., 'openai', 'aws-bedrock', etc.",
    responses={
        200: {"description": "List of currently configured and active providers."},
        500: {"description": "Internal Server Error. Check logs for more details."}
    }
)
async def get_providers(
        client: Client = Depends(get_client),
        logger: Logger = Depends(get_logger)
) -> ActiveProvidersResponse:
    try:
        logger.info("Fetching providers")
        return ActiveProvidersResponse(Providers=client.provider_configs.keys())

    except Exception as e:
        logger.error(f"Error fetching providers: {e}")
        raise HTTPException(status_code=500)


# Global exception handler for dependency errors
@app.exception_handler(ValueError)
async def value_error_handler(
        request: Request,  # could use for more info later
        exc: ValueError
) -> Response:
    logging.error(f"Internal dependency issue -> {exc}")
    return Response(status_code=500)
