from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests
import os
from dotenv import load_dotenv
load_dotenv()

class WebSearchToolInput(BaseModel):
    """Input schema for WebSearchTool."""
    query: str = Field(..., description="The search query to send to Tavily.")


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Searches the web using the Tavily Search API and returns a concise summary "
        "of the top relevant results. Useful for retrieving definitions, examples, "
        "and up-to-date information about a specific topic. " 
        "Input must be a plain text query string — do not wrap it in JSON."
    )
    args_schema: Type[BaseModel] = WebSearchToolInput

    def _parse_args(self, raw_args):
        # This runs BEFORE Pydantic validation
        if isinstance(raw_args, dict) and "query" in raw_args:
            raw_args["query"] = str(raw_args["query"])  # force string
        elif isinstance(raw_args, dict):
            raw_args = {"query": str(list(raw_args.values())[0])}
        return super()._parse_args(raw_args)

    def _run(self, query: str) -> str:
        """Perform a Tavily search and return summarized results."""
        # Handle case where model sends a dict instead of str
        if isinstance(query, dict):
            query = query.get("description") or query.get("text") or str(query)
        try:
            # CrewAI sometimes passes a dict instead of string
            if isinstance(query, dict):
                # Try to extract the description if present
                if "description" in query:
                    query = query["description"]
                else:
                    # fallback to first value in dict
                    query = list(query.values())[0]

            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if not tavily_api_key:
                raise ValueError("Missing TAVILY_API_KEY in environment variables.")

            api_url = "https://api.tavily.com/search"

            payload = {
                "api_key": tavily_api_key,
                "query": query,
                "search_depth": "advanced",  # can be 'basic' or 'advanced'
                "max_results": 3,
                "timeout": 5,
                "include_answer": True,      # return summarized text
                "include_domains": [],       # optionally restrict domains
                "include_raw_content": False
            }

            response = requests.post(api_url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Extract answer or summarized text
            answer = data.get("answer")
            results = data.get("results", [])

            text_parts = []
            if answer:
                text_parts.append(f"**Summary:** {answer}")

            for res in results[:3]:
                title = res.get("title", "")
                url = res.get("url", "")
                content = res.get("content", "")
                snippet = (content[:200] + "...") if len(content) > 200 else content
                text_parts.append(f"- {title}: {snippet} ({url})")

            if not text_parts:
                text_parts.append("No summary available, please refine your query.")

            return "\n".join(text_parts)

        except Exception as e:
            return f"Web search failed: {str(e)}"
