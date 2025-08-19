from fastmcp import FastMCP

mcp = FastMCP(name="calculator")

@mcp.tool
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers together."""
    return a * b


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        path="/",
    )
