#!/usr/bin/env python3
"""
Simple Elasticsearch MCP Server using FastMCP
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict

import httpx
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("elasticsearch-mcp")

# Elasticsearch configuration - use environment variable
ELASTICSEARCH_URL = os.getenv("ES_URL", "http://localhost:9400")

# Create FastMCP server instance
mcp = FastMCP("elasticsearch-mcp")

@mcp.tool()
def list_indices(indexPattern: str = "*") -> str:
    """List all available Elasticsearch indices matching the index pattern"""
    try:
        with httpx.Client(timeout=30.0) as client:
            if indexPattern == "*":
                # Get all indices when pattern is "*"
                response = client.get(f"{ELASTICSEARCH_URL}/_cat/indices?format=json")
            else:
                # Use pattern to filter indices
                response = client.get(f"{ELASTICSEARCH_URL}/_cat/indices/{indexPattern}?format=json")
            
            response.raise_for_status()
            indices = response.json()
            
            result = []
            for index in indices:
                result.append({
                    "index": index.get("index", ""),
                    "docs_count": index.get("docs.count", "0"),
                    "store_size": index.get("store.size", "0"),
                    "health": index.get("health", "unknown")
                })
            
            return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error listing indices: {e}")
        return f"Error listing indices: {str(e)}"

@mcp.tool()
def search(index: str, queryBody: Dict[str, Any]) -> str:
    """Perform an Elasticsearch search with the provided query DSL. Highlights are always enabled."""
    try:
        if not index:
            return "Error: index parameter is required"
        
        if not queryBody:
            return "Error: queryBody parameter is required"
        
        with httpx.Client(timeout=30.0) as client:
            # Enable highlights by default as mentioned in official docs
            if "highlight" not in queryBody:
                queryBody["highlight"] = {
                    "fields": {"*": {}}
            }
            
            response = client.post(
                f"{ELASTICSEARCH_URL}/{index}/_search",
                json=queryBody,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error searching index {index}: {e}")
        return f"Error searching index {index}: {str(e)}"

@mcp.tool()
def get_mappings(index: str) -> str:
    """Get field mappings for a specific Elasticsearch index"""
    try:
        if not index:
            return "Error: index parameter is required"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{ELASTICSEARCH_URL}/{index}/_mapping")
            response.raise_for_status()
            mappings = response.json()
            
            return json.dumps(mappings, indent=2)
    except Exception as e:
        logger.error(f"Error getting mappings for index {index}: {e}")
        return f"Error getting mappings for index {index}: {str(e)}"

@mcp.tool()
def get_shards(index: str = None) -> str:
    """Get shard information for all or specific indices"""
    try:
        with httpx.Client(timeout=30.0) as client:
            if index:
                url = f"{ELASTICSEARCH_URL}/_cat/shards/{index}?format=json"
            else:
                url = f"{ELASTICSEARCH_URL}/_cat/shards?format=json"
            
            response = client.get(url)
            response.raise_for_status()
            shards = response.json()
            
            result = []
            for shard in shards:
                result.append({
                    "index": shard.get("index", ""),
                    "shard": shard.get("shard", ""),
                    "prirep": shard.get("prirep", ""),
                    "state": shard.get("state", ""),
                    "docs": shard.get("docs", ""),
                    "store": shard.get("store", ""),
                    "node": shard.get("node", "")
                })
            
            return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting shard information: {e}")
        return f"Error getting shard information: {str(e)}"

if __name__ == "__main__":
    mcp.run() 