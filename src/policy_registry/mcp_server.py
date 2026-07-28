from __future__ import annotations

from .registry import PolicyRegistry


def create_server(registry_path: str | None = None):
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("MCP-Extra fehlt: pip install 'policy-registry[mcp]'") from exc

    server = FastMCP("policy-registry")
    registry = PolicyRegistry(registry_path)

    @server.tool()
    def policy_search(query: str = "", scope: str = "", consumer: str = ""):
        """Find metadata pointers without copying canonical policy text."""
        return registry.search(query, scope=scope or None, consumer=consumer or None)

    @server.tool()
    def policy_get(entry_id: str):
        """Return one registry entry by stable id."""
        return registry.get(entry_id)

    @server.tool()
    def policy_resolve(scope: str, query: str = "", consumer: str = ""):
        """Resolve explicit norms; return TOM-lm advisory fallback when unresolved."""
        return registry.resolve(scope=scope, query=query, consumer=consumer or None)

    return server


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()

