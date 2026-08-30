"""
Tools module for the MCP server.

This module defines all the tools (functions) that the MCP server exposes to clients.
Tools are the core functionality of an MCP server - they are callable functions that
AI assistants and other clients can invoke to perform specific actions.

Each tool should:
- Have a clear, descriptive name
- Include comprehensive docstrings (used by AI to understand when to call the tool)
- Return structured data (typically dict or list)
- Handle errors gracefully
"""

import html
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from server import utils

ALLOWED_DOCUMENTATION_HOSTS = {"docs.databricks.com"}
ICON_VOLUME_PATH = "/Volumes/databricks_architect_agent/agent_demo/architecture_icons"
ARTIFACT_VOLUME_PATH = "/Volumes/databricks_architect_agent/agent_demo/architecture_artifacts"


def _plain_text(document: str) -> str:
    """Extract bounded, readable text from an official documentation HTML page."""
    without_scripts = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", document, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", without_scripts))).strip()


def _mermaid_from_spec(specification: dict) -> str:
    """Validate the bounded node and edge contract before producing Mermaid."""
    nodes, edges = specification.get("nodes"), specification.get("edges", [])
    if not isinstance(nodes, list) or not nodes or not isinstance(edges, list):
        raise ValueError("specification requires a non-empty nodes array and an edges array")
    identifiers = set()
    lines = ["flowchart LR"]
    for node in nodes:
        identifier = str(node.get("id", ""))
        label = str(node.get("label", identifier)).replace("[", "(").replace("]", ")")
        if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", identifier):
            raise ValueError("node IDs must use 1-64 ASCII letters, digits, or underscores")
        identifiers.add(identifier)
        lines.append(f"  {identifier}[{label}]")
    for edge in edges:
        if edge.get("from") not in identifiers or edge.get("to") not in identifiers:
            raise ValueError("each edge must reference declared node IDs")
        lines.append(f"  {edge['from']} --> {edge['to']}")
    return "\n".join(lines)


def load_tools(mcp_server):
    """
    Register all MCP tools with the server.

    This function is called during server initialization to register all available
    tools with the MCP server instance. Tools are registered using the @mcp_server.tool
    decorator, which makes them available to clients via the MCP protocol.

    Args:
        mcp_server: The FastMCP server instance to register tools with. This is the
                   main server object that handles tool registration and routing.

    Example:
        To add a new tool, define it within this function using the decorator:

        @mcp_server.tool
        def my_new_tool(param: str) -> dict:
            '''Description of what the tool does.'''
            return {"result": f"Processed {param}"}
    """

    @mcp_server.tool
    def health() -> dict:
        """
        Check the health of the MCP server and Databricks connection.

        This is a simple diagnostic tool that confirms the server is running properly.
        It's useful for:
        - Monitoring and health checks
        - Testing the MCP connection
        - Verifying the server is responsive

        Returns:
            dict: A dictionary containing:
                - status (str): The health status ("healthy" if operational)
                - message (str): A human-readable status message

        Example response:
            {
                "status": "healthy",
                "message": "Custom MCP Server is healthy and connected to Databricks Apps."
            }
        """
        return {
            "status": "healthy",
            "message": "Databricks Solutions Architect knowledge MCP server is healthy.",
            "allowed_documentation_hosts": sorted(ALLOWED_DOCUMENTATION_HOSTS),
            "icon_volume_path": ICON_VOLUME_PATH,
        }

    @mcp_server.tool
    def fetch_official_databricks_document(url: str) -> dict:
        """Fetch one public, official Databricks documentation page as unreviewed candidate evidence.

        Only docs.databricks.com is allowed. The returned content is evidence for
        review, not an affirmative architecture claim. A reviewer must promote
        extracted claims to REVIEWED in the governed knowledge tables first.
        """
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOCUMENTATION_HOSTS:
            raise ValueError("Only HTTPS URLs hosted by docs.databricks.com are allowed")
        request = Request(url, headers={"User-Agent": "enterprise-architect-mcp/1.0"})
        with urlopen(request, timeout=15) as response:
            content = response.read(1_000_000).decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        text = _plain_text(content)
        return {
            "canonical_url": url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": sha256(content.encode("utf-8")).hexdigest(),
            "review_status": "CANDIDATE",
            "text_excerpt": text[:8000],
            "next_step": "Stage extracted claims in architecture_knowledge_item and require explicit human review before recommendation use.",
        }

    @mcp_server.tool
    def validate_architecture_diagram(specification_json: str) -> dict:
        """Validate an architecture graph and produce Mermaid plus governed icon/artifact locations.

        This tool does not provision infrastructure. Pass its valid specification
        to the controlled diagram-renderer workflow to create PROPOSED Mermaid,
        SVG, and PNG files in the governed artifact Volume.
        """
        specification = json.loads(specification_json)
        mermaid = _mermaid_from_spec(specification)
        icons = []
        for node in specification["nodes"]:
            icon_name = node.get("icon")
            if icon_name:
                if not re.fullmatch(r"[a-z0-9-]+", str(icon_name)):
                    raise ValueError("icon names must contain lowercase letters, digits, and hyphens")
                icons.append(f"{ICON_VOLUME_PATH}/icons/svg/{icon_name}.svg")
        return {
            "status": "VALIDATED",
            "mermaid": mermaid,
            "icon_paths": icons,
            "render_workflow": "dev-enterprise-architect-diagram-renderer",
            "artifact_volume_path": ARTIFACT_VOLUME_PATH,
            "artifact_status": "PROPOSED",
        }

    @mcp_server.tool
    def get_current_user() -> dict:
        """
        Get information about the current authenticated user.

        This tool retrieves details about the user who is currently authenticated
        with the MCP server. When deployed as a Databricks App, this returns
        information about the end user making the request. When running locally,
        it returns information about the developer's Databricks identity.

        Useful for:
        - Personalizing responses based on the user
        - Authorization checks
        - Audit logging
        - User-specific operations

        Returns:
            dict: A dictionary containing:
                - display_name (str): The user's display name
                - user_name (str): The user's username/email
                - active (bool): Whether the user account is active

        Example response:
            {
                "display_name": "John Doe",
                "user_name": "john.doe@example.com",
                "active": true
            }

        Raises:
            Returns error dict if authentication fails or user info cannot be retrieved.
        """
        try:
            w = utils.get_user_authenticated_workspace_client()
            user = w.current_user.me()
            return {
                "display_name": user.display_name,
                "user_name": user.user_name,
                "active": user.active,
            }
        except Exception as e:
            return {"error": str(e), "message": "Failed to retrieve user information"}

    """
    TODO: Add more tools as necessary
    """
