#!/usr/bin/env python3
"""
Simple test for new schema analysis functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to Python path  
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from mcp_postgresql_ops.functions import execute_query

async def simple_schema_test():
    """Simple test to verify database connectivity and basic schema queries"""
    
    print("Testing Database Schema Connectivity")
    print("=" * 40)
    
    try:
        # Test basic connectivity
        print("1. Testing basic connectivity...")
        result = await execute_query("SELECT version()", database="ecommerce")
        if result:
            print(f"✅ Connected to: {result[0]['version'][:50]}...")
        else:
            print("❌ No result from version query")
            return 1
            
        # Test table existence
        print("\n2. Testing table list query...")
        result = await execute_query("""
            SELECT table_schema, table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog') 
            ORDER BY table_schema, table_name 
            LIMIT 5
        """, database="ecommerce")
        
        if result:
            print(f"✅ Found {len(result)} tables:")
            for row in result:
                print(f"  - {row['table_schema']}.{row['table_name']} ({row['table_type']})")
        else:
            print("❌ No tables found")
            
        # Test foreign key query
        print("\n3. Testing foreign key relationships query...")
        result = await execute_query("""
            SELECT 
                tc.table_name as child_table,
                ccu.table_name as parent_table,
                string_agg(kcu.column_name, ', ') as columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.referential_constraints rc ON tc.constraint_name = rc.constraint_name
            JOIN information_schema.constraint_column_usage ccu ON rc.unique_constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema NOT IN ('information_schema', 'pg_catalog')
            GROUP BY tc.table_name, ccu.table_name
            LIMIT 3
        """, database="ecommerce")
        
        if result:
            print(f"✅ Found {len(result)} foreign key relationships:")
            for row in result:
                print(f"  - {row['child_table']} → {row['parent_table']} ({row['columns']})")
        else:
            print("⚠️  No foreign key relationships found (this is ok for test data)")
            
        print("\n✅ Schema connectivity test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ.setdefault("POSTGRES_HOST", "localhost")
    os.environ.setdefault("POSTGRES_PORT", "15432")
    os.environ.setdefault("POSTGRES_USER", "postgres")
    os.environ.setdefault("POSTGRES_PASSWORD", "changeme!@34")
    
    # Run the tests
    exit_code = asyncio.run(simple_schema_test())
    sys.exit(exit_code)
