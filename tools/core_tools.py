
from typing import Annotated
from config import MY_NUMBER, RESUME_FILE
from pathlib import Path
import markdownify
import readabilipy
# from mcp import tool
# from fastmcp import mcp
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, TextContent
from mcp import ErrorData, McpError
from openai import BaseModel
from pydantic import AnyUrl, Field

def register_core_tools(mcp):

    class RichToolDescription(BaseModel):
        description: str
        use_when: str
        side_effects: str | None

    ResumeToolDescription = RichToolDescription(
        description="Serve your resume in plain markdown.",
        use_when="Puch (or anyone) asks for your resume; this must return raw markdown, no extra formatting.",
        side_effects=None,
    )

    @mcp.tool(description=ResumeToolDescription.model_dump_json())
    async def resume() -> str:
        """Return your resume exactly as markdown text."""
        try:
            resume_path = Path(RESUME_FILE)
            if not resume_path.exists():
                raise FileNotFoundError("Resume file not found")
            return resume_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"<error>Could not retrieve resume: {e}</error>"

    @mcp.tool
    async def validate() -> str:
        """Returns the configured phone number for verification."""
        return MY_NUMBER

    class Fetch:
        IGNORE_ROBOTS_TXT = True
        USER_AGENT = "Puch/1.0 (Autonomous)"

        @classmethod
        async def fetch_url(cls, url: str, user_agent: str, force_raw: bool = False) -> tuple[str, str]:
            from httpx import AsyncClient, HTTPError
            async with AsyncClient() as client:
                try:
                    response = await client.get(url, follow_redirects=True, headers={"User-Agent": user_agent}, timeout=30)
                except HTTPError as e:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}"))
                if response.status_code >= 400:
                    raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url} - status code {response.status_code}"))
                page_raw = response.text

            content_type = response.headers.get("content-type", "")
            is_page_html = "<html" in page_raw[:100] or "text/html" in content_type or not content_type

            if is_page_html and not force_raw:
                return cls.extract_content_from_html(page_raw), ""
            return (page_raw, f"Content type {content_type} cannot be simplified to markdown, but here is the raw content:\n")

        @staticmethod
        def extract_content_from_html(html: str) -> str:
            ret = readabilipy.simple_json.simple_json_from_html_string(html, use_readability=True)
            if not ret["content"]:
                return "<error>Page failed to be simplified from HTML</error>"
            content = markdownify.markdownify(ret["content"], heading_style=markdownify.ATX)
            return content

    FetchToolDescription = RichToolDescription(
        description="Fetch a URL and return its content.",
        use_when="Use this tool when the user provides a URL and asks for its content, or when the user wants to fetch a webpage.",
        side_effects="Returns simplified markdown or raw HTML content from the provided URL."
    )

    @mcp.tool(description=FetchToolDescription.model_dump_json())
    async def fetch(
        url: Annotated[AnyUrl, Field(description="URL to fetch")],
        max_length: Annotated[int, Field(default=5000, gt=0, lt=1000000)] = 5000,
        start_index: Annotated[int, Field(default=0, ge=0)] = 0,
        raw: Annotated[bool, Field(default=False)] = False,
    ) -> list[TextContent]:
        content, prefix = await Fetch.fetch_url(str(url), Fetch.USER_AGENT, force_raw=raw)
        original_length = len(content)
        if start_index >= original_length:
            content = "<error>No more content available.</error>"
        else:
            truncated_content = content[start_index : start_index + max_length]
            if not truncated_content:
                content = "<error>No more content available.</error>"
            else:
                content = truncated_content
                actual_content_length = len(truncated_content)
                remaining_content = original_length - (start_index + actual_content_length)
                if actual_content_length == max_length and remaining_content > 0:
                    next_start = start_index + actual_content_length
                    content += f"\n\n<error>Content truncated. Call the fetch tool with a start_index of {next_start} to get more content.</error>"
        return [TextContent(type="text", text=f"{prefix}Contents of {url}:\n{content}")]
