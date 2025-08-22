#!/usr/bin/env python3
"""
Test script for new schema analysis tools
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from mcp_postgresql_ops.mcp_main import (
    get_table_schema,
    get_database_schema_overview,
    get_table_relationships
)

async def test_schema_tools():
    """Test the new schema analysis tools"""
    
    print("Testing New Schema Analysis Tools")
    print("=" * 50)
    
    try:
        # Test 1: Database Schema Overview
        print("\n1. Testing get_database_schema_overview...")
        result = await get_database_schema_overview(limit=10, database_name="ecommerce")
        print(f"Result length: {len(result)} characters")
        print("First 500 characters:")
        print(result[:500])
        print("...")
        
        # Test 2: Table Schema for a known table
        print("\n2. Testing get_table_schema for 'products'...")
        result = await get_table_schema("products", database_name="ecommerce")
        print(f"Result length: {len(result)} characters")
        print("First 500 characters:")
        print(result[:500])
        print("...")
        
        # Test 3: Table Relationships
        print("\n3. Testing get_table_relationships...")
        result = await get_table_relationships(database_name="ecommerce")
        print(f"Result length: {len(result)} characters")
        print("First 500 characters:")
        print(result[:500])
        print("...")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "5432")
    os.environ.setdefault("POSTGRES_USER", "postgres")
    os.environ.setdefault("POSTGRES_PASSWORD", "postgres123")
    
    # Run the tests
    exit_code = asyncio.run(test_schema_tools())
    sys.exit(exit_code)
