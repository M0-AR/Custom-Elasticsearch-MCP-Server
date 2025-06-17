FROM python:3.11-slim

# Install required packages
RUN pip install mcp httpx

# Create app directory
WORKDIR /app

# Copy the MCP server file
COPY simple_elasticsearch_mcp.py .

# Make it executable
RUN chmod +x simple_elasticsearch_mcp.py

# Run the MCP server
CMD ["python3", "simple_elasticsearch_mcp.py"] 