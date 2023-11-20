from contextlib import contextmanager, asynccontextmanager
from uuid import UUID
from contextvars import ContextVar
from langchain.schema.output import ChatGenerationChunk, GenerationChunk, LLMResult
from typing import Generator, AsyncGenerator, Callable, Coroutine, Awaitable, Any
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema.messages import BaseMessage


class AsyncStreamHandler(AsyncCallbackHandler):
    """Async callback handler that can be used to handle callbacks from langchain."""
    
    def __init__(self, fn: Callable[[str], Awaitable[None] | None], default_kwargs: dict) -> None:
        self.fn = fn
        self.default_kwargs = default_kwargs
        self.cost: float = 0.0
        self.tokens: int = 0
    
    async def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        pass
    
    async def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: GenerationChunk | ChatGenerationChunk | None = None,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        if isinstance(self.fn, Coroutine):
            await self.fn(token, **self.default_kwargs)
        else:
            self.fn(token, **self.default_kwargs)
    
    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        if self.fn is print:
            print("\n")


stream_handler: ContextVar[AsyncStreamHandler | None] = ContextVar("stream_handler", default=None)


@contextmanager
def stream_to(fn: Callable[[str], None], **kwargs: Any) -> Generator[AsyncStreamHandler, None, None]:
    """
    Stream the llm tokens to a given function.

    Example:
        >>> with stream_to(print):
        ...     # your chain calls here
    """
    if fn is print and kwargs == {}:
        kwargs = {"end": "", "flush": True}
    cb = AsyncStreamHandler(fn, kwargs)
    stream_handler.set(cb)
    yield cb
    stream_handler.set(None)


@asynccontextmanager
async def astream_to(fn: Callable[[str], Awaitable[None] | None], **kwargs: Any) -> AsyncGenerator[AsyncStreamHandler, None]:
    """
    Asyncronously stream the llm tokens to a given function.
    
    Example:
        >>> async with astream_to(print):
        ...     # your chain calls here
    """
    if fn is print and kwargs == {}:
        kwargs = {"end": "", "flush": True}
    cb = AsyncStreamHandler(fn, kwargs)
    stream_handler.set(cb)
    yield cb
    stream_handler.set(None)