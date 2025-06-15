# Quickstart: Adding a Manual Connector

This project can generate connectors automatically via the `connector_gen` service, but you can also add one manually.

1. **Create your FastAPI connector**
   - Implement a FastAPI application that exposes your MCP tool using [`fastapi-mcp`](https://pypi.org/project/fastapi-mcp/).
   - Make sure the app exposes a health endpoint at `/health` returning status code `200`.

2. **Build and run in Docker**
   - Create a Dockerfile based on `python:3.11-slim`.
   - Install your dependencies and run the app with `uvicorn`.
   - Expose port `8000`.

3. **Register the connector**
   - Start the container and note the exposed port.
   - Add the connector URL to Redis using:
     ```bash
     HSET connectors <tool_name> http://localhost:<port>
     ```

Once registered, the system will route requests to your manual connector.
