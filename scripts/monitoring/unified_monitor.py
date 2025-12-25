#!/usr/bin/env python3
# unified_monitor.py

import psycopg2
import chromadb
from datetime import datetime
import json
import os
import sys

# Configuration
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = int(os.getenv('PG_PORT', 5432))
PG_DB = os.getenv('PG_DB', 'gaji_db')
PG_USER = os.getenv('PG_USER', 'gaji_user')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'password')

CHROMA_HOST = os.getenv('CHROMA_HOST', 'localhost')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', 8000))

LOG_DIR = os.getenv('LOG_DIR', './logs/monitoring')

class UnifiedMonitor:
    def __init__(self):
        print(f"Connecting to PostgreSQL at {PG_HOST}:{PG_PORT}...")
        try:
            self.pg_conn = psycopg2.connect(
                host=PG_HOST,
                port=PG_PORT,
                database=PG_DB,
                user=PG_USER,
                password=PG_PASSWORD
            )
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            self.pg_conn = None
        
        print(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
        try:
            self.chroma_client = chromadb.HttpClient(
                host=CHROMA_HOST,
                port=CHROMA_PORT
            )
        except Exception as e:
            print(f"Failed to connect to ChromaDB: {e}")
            self.chroma_client = None
    
    def get_pg_stats(self):
        """PostgreSQL Stats"""
        if not self.pg_conn:
            return {}
            
        try:
            cursor = self.pg_conn.cursor()
            
            # Cache Hit Ratio
            cursor.execute("""
                SELECT ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) 
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
            res = cursor.fetchone()
            cache_hit_ratio = res[0] if res else 0
            
            # Connections
            cursor.execute("SELECT COUNT(*) FROM pg_stat_activity")
            connections = cursor.fetchone()[0]
            
            # DB Size
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            db_size = cursor.fetchone()[0]
            
            cursor.close()
            
            return {
                'cache_hit_ratio': float(cache_hit_ratio) if cache_hit_ratio else 0,
                'connections': connections,
                'database_size': db_size
            }
        except Exception as e:
            print(f"Error getting PG stats: {e}")
            return {}
    
    def get_chroma_stats(self):
        """ChromaDB Stats"""
        if not self.chroma_client:
            return {}
            
        try:
            collections = self.chroma_client.list_collections()
            total_docs = 0
            for col in collections:
                try:
                    collection = self.chroma_client.get_collection(col.name)
                    total_docs += collection.count()
                except:
                    pass
            
            return {
                'collections_count': len(collections),
                'total_documents': total_docs,
                'estimated_memory_mb': round((total_docs * 6) / 1024, 2)
            }
        except Exception as e:
            print(f"Error getting Chroma stats: {e}")
            return {}
    
    def generate_report(self):
        """Generate Unified Report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'postgresql': self.get_pg_stats(),
            'chromadb': self.get_chroma_stats()
        }
        
        # Console Output
        print(f"\n{'='*60}")
        print(f"Unified Monitoring Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        if report['postgresql']:
            print(f"\n[PostgreSQL]")
            print(f"  Cache Hit Ratio: {report['postgresql'].get('cache_hit_ratio', 'N/A')}%")
            print(f"  Connections: {report['postgresql'].get('connections', 'N/A')}")
            print(f"  DB Size: {report['postgresql'].get('database_size', 'N/A')}")
        
        if report['chromadb']:
            print(f"\n[ChromaDB]")
            print(f"  Collections: {report['chromadb'].get('collections_count', 'N/A')}")
            print(f"  Total Docs: {report['chromadb'].get('total_documents', 'N/A')}")
            print(f"  Est. Memory: {report['chromadb'].get('estimated_memory_mb', 'N/A')} MB")
        
        # Save to JSON
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
            
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'{LOG_DIR}/unified_report_{date_str}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nReport saved to {report_file}")
        return report
    
    def close(self):
        if self.pg_conn:
            self.pg_conn.close()

# Run
if __name__ == '__main__':
    monitor = UnifiedMonitor()
    monitor.generate_report()
    monitor.close()
