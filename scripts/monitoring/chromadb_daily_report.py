#!/usr/bin/env python3
# chromadb_daily_report.py

import chromadb
import time
from datetime import datetime
import json
import os
import sys

# Configuration
# If running from host, you might need to port-forward or use the container IP
CHROMA_HOST = os.getenv('CHROMA_HOST', 'localhost')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', 8000))
LOG_DIR = os.getenv('LOG_DIR', './logs/monitoring')

def generate_daily_report():
    """ChromaDB Daily Report"""
    print(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}...")
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        heartbeat = client.heartbeat()
        print(f"Connected. Heartbeat: {heartbeat}")
    except Exception as e:
        print(f"Failed to connect to ChromaDB: {e}")
        return

    report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'timestamp': datetime.now().isoformat(),
        'collections': []
    }
    
    try:
        collections = client.list_collections()
        total_docs = 0
        
        for col in collections:
            try:
                collection = client.get_collection(col.name)
                count = collection.count()
                total_docs += count
                
                # Sample query performance
                start = time.time()
                collection.query(query_texts=["test"], n_results=5)
                query_time = (time.time() - start) * 1000
                
                col_stats = {
                    'name': col.name,
                    'document_count': count,
                    'avg_query_time_ms': round(query_time, 2)
                }
                
                report['collections'].append(col_stats)
                
            except Exception as e:
                print(f"Error processing collection {col.name}: {e}")
        
        report['total_documents'] = total_docs
        report['total_collections'] = len(collections)
        # Approx memory usage: 6KB per doc (1536 float32 + metadata)
        report['estimated_memory_mb'] = round((total_docs * 6) / 1024, 2)
        
        # Save to JSON
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
            
        report_file = f"{LOG_DIR}/chromadb_report_{report['date']}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report generated: {report_file}")
        return report

    except Exception as e:
        print(f"Error generating report: {e}")

if __name__ == '__main__':
    generate_daily_report()
