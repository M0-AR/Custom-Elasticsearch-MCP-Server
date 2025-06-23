# Custom Elasticsearch MCP Server

A simple MCP (Model Context Protocol) server for Elasticsearch designed for cloud environments where your public key is already authorized on the server.

## Why This Custom Version?

**No API Key Required** - Unlike the official Elasticsearch MCP server that requires both `ES_URL` and `ES_API_KEY`, this version only needs the URL since your public key is already trusted on the cloud server.

**Enhanced Tools** - Better usability with optional parameters and improved defaults compared to the official version.

## What This Does

This MCP server connects Cursor to your Elasticsearch cluster with 4 powerful tools:
- **`list_indices`** - List all indices (optional pattern filter)
- **`search`** - Full Elasticsearch Query DSL support
- **`get_mappings`** - Get field mappings for any index
- **`get_shards`** - View cluster shard information

## Quick Start

### Build from Source
```bash
git clone https://github.com/M0-AR/Custom-Elasticsearch-MCP-Server.git
cd Custom-Elasticsearch-MCP-Server
docker build -t elasticsearch-mcp:latest .
```

### 2. Add to Cursor MCP Configuration
Add this to your `.cursor/mcp.json` file:

**Configuration:**
```json
{
    "mcpServers": {
        "elasticsearch-custom": {
            "command": "docker",
            "args": [
                "run",
                "-i",
                "--rm",
                "--add-host=host.docker.internal:host-gateway",
                "-e",
                "ES_URL=http://host.docker.internal:9400",
                "elasticsearch-mcp:latest"
            ]
        }
    }
}
```

### 3. Restart Cursor
Close and reopen Cursor. You should see the elasticsearch-custom server with 4 tools enabled.

## Configuration

**Environment Variables:**
- `ES_URL` - Your Elasticsearch URL (default: `http://localhost:9400`)

**For different Elasticsearch ports:**
```json
"ES_URL=http://host.docker.internal:9200"
```

## Example Usage

Once connected in Cursor, you can:

- **List all indices:** "Show me all elasticsearch indices"
- **Search data:** "Search for sales data in hq.sales index"  
- **Get mappings:** "What fields are in the hq.menuitems index?"
- **Check cluster:** "Show me the elasticsearch cluster status"

## Comparison with Official Server

| Feature | Official Server | This Custom Server |
|---------|----------------|-------------------|
| **Authentication** | Requires `ES_URL` + `ES_API_KEY` | Only needs `ES_URL` (public key authorized) |
| **list_indices** | Requires `indexPattern` parameter | Optional parameter with "*" default |
| **Tools Available** | 4 tools (same functions) | 4 tools (enhanced usability) |
| **Security** | API key based | Public key authorization |

## Files

- `simple_elasticsearch_mcp.py` - Main MCP server
- `Dockerfile` - Container build instructions  
- `requirements.txt` - Python dependencies

## Manual Testing

### Test the server directly:
```bash
python3 simple_elasticsearch_mcp.py
```

### Test with JSON-RPC commands:

**1. List all tools:**
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | python3 simple_elasticsearch_mcp.py
```

**2. List all indices:**
```bash
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "list_indices", "arguments": {}}}' | python3 simple_elasticsearch_mcp.py
```

**3. Search for data:**
```bash
echo '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search", "arguments": {"index": "hq.sales", "queryBody": {"query": {"match_all": {}}, "size": 3}}}}' | python3 simple_elasticsearch_mcp.py
```

**4. Get index mappings:**
```bash
echo '{"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "get_mappings", "arguments": {"index": "hq.menuitems"}}}' | python3 simple_elasticsearch_mcp.py
```

**5. Check cluster shards:**
```bash
echo '{"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "get_shards", "arguments": {}}}' | python3 simple_elasticsearch_mcp.py
```

### Set custom Elasticsearch URL:
```bash
ES_URL="http://your-es-host:9200" python3 simple_elasticsearch_mcp.py
```

## Troubleshooting

### **❌ "Connection refused" or "timed out" errors**

**Root Cause:** The most common issue is Docker container networking when Elasticsearch is accessible via SSH tunnel.

**Solution:** Ensure these requirements are met:

#### **1. SSH Tunnel Must Be Active**
If your Elasticsearch is behind SSH tunnel (common for cloud deployments):
```bash
# Start SSH tunnel to forward port 9400
ssh -L 9400:localhost:9400 -N -f -l username your-server-ip

# Verify tunnel is working
curl -X GET "localhost:9400/_cluster/health?pretty"
```

#### **2. Correct Docker Configuration**
Your `mcp.json` should use **exactly** this configuration:
```json
"elasticsearch-custom": {
    "command": "docker",
    "args": [
        "run",
        "-i",
        "--rm",
        "--add-host=host.docker.internal:host-gateway",
        "-e",
        "ES_URL=http://host.docker.internal:9400",
        "elasticsearch-mcp:latest"
    ]
}
```

**Key Points:**
- ✅ Use `--add-host=host.docker.internal:host-gateway` (not IP addresses)
- ✅ Use `ES_URL=http://host.docker.internal:9400` (not localhost)
- ✅ SSH tunnel must be running before starting Cursor

#### **3. Test Docker Connectivity**
```bash
# Test if Docker can reach your Elasticsearch
docker run --rm --add-host=host.docker.internal:host-gateway alpine/curl \
  curl -s http://host.docker.internal:9400/_cluster/health
```

#### **4. Complete MCP Docker Test**
Test the full MCP workflow with this comprehensive command:
```bash
# Full MCP server test with proper initialization
{
    echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}';
    echo '{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}';
    echo '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "list_indices", "arguments": {}}}';
} | docker run -i --rm --add-host=host.docker.internal:host-gateway -e ES_URL="http://host.docker.internal:9400" elasticsearch-mcp:latest
```

**Expected Output:**
- Initialization response with server info
- List of all Elasticsearch indices in JSON format
- No error messages

#### **5. Alternative: Network Host Mode**
If `host-gateway` doesn't work, try network host mode:
```json
"args": [
    "run", "-i", "--rm", "--network=host",
    "-e", "ES_URL=http://localhost:9400",
    "elasticsearch-mcp:latest"
]
```

### **❌ "Received request before initialization was complete"**

**Root Cause:** MCP protocol requires proper initialization sequence.

**Solution:** Always initialize before calling tools:
```bash
# Correct sequence:
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}'
echo '{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}'
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "list_indices", "arguments": {}}}'
```

## That's It! 

Build → Add to config → Restart Cursor → Done! 🚀 