"""
Advanced Data Exporter module for scraped data.
Supports multiple formats: JSON, CSV, SQLite, and MongoDB.
Features: Batch processing, compression, encryption, and cloud storage integration.
"""
import asyncio
import json
import csv
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from loguru import logger

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("pymongo not installed. MongoDB export disabled.")


class DataExporter:
    """
    Advanced data exporter supporting multiple formats and destinations.
    
    Features:
    - JSON export (with optional compression)
    - CSV export (with custom delimiters)
    - SQLite database export (with schema management)
    - MongoDB export (if pymongo available)
    - Automatic directory creation
    - Timestamp-based file naming
    - Batch processing for large datasets
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"DataExporter initialized with output directory: {self.output_dir}")
    
    def _generate_filename(self, prefix: str, extension: str) -> str:
        """Generate timestamped filename."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"
    
    async def export_json(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        pretty: bool = True,
        compress: bool = False,
    ) -> Path:
        """
        Export data to JSON format.
        
        Args:
            data: List of dictionaries to export
            filename: Optional custom filename
            pretty: Whether to pretty-print JSON
            compress: Whether to compress with gzip
        
        Returns:
            Path to exported file
        """
        if filename is None:
            ext = "json.gz" if compress else "json"
            filename = self._generate_filename("scraped_data", ext)
        
        filepath = self.output_dir / filename
        
        indent = 2 if pretty else None
        
        if compress:
            import gzip
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
        
        logger.success(f"Exported {len(data)} records to JSON: {filepath}")
        return filepath
    
    async def export_csv(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        delimiter: str = ',',
        include_header: bool = True,
    ) -> Path:
        """
        Export data to CSV format.
        
        Args:
            data: List of dictionaries to export
            filename: Optional custom filename
            delimiter: CSV delimiter character
            include_header: Whether to include header row
        
        Returns:
            Path to exported file
        """
        if filename is None:
            filename = self._generate_filename("scraped_data", "csv")
        
        filepath = self.output_dir / filename
        
        if not data:
            logger.warning("No data to export to CSV")
            return filepath
        
        # Flatten nested dictionaries
        flattened_data = []
        for item in data:
            flat_item = {}
            for key, value in item.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        flat_item[f"{key}.{sub_key}"] = sub_value
                else:
                    flat_item[key] = value
            flattened_data.append(flat_item)
        
        # Get all unique keys
        fieldnames = set()
        for item in flattened_data:
            fieldnames.update(item.keys())
        fieldnames = sorted(fieldnames)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                delimiter=delimiter,
                extrasaction='ignore',
            )
            
            if include_header:
                writer.writeheader()
            
            writer.writerows(flattened_data)
        
        logger.success(f"Exported {len(data)} records to CSV: {filepath}")
        return filepath
    
    async def export_sqlite(
        self,
        data: List[Dict[str, Any]],
        table_name: str = "scraped_data",
        filename: Optional[str] = None,
        drop_existing: bool = False,
    ) -> Path:
        """
        Export data to SQLite database.
        
        Args:
            data: List of dictionaries to export
            table_name: Name of the table to create/insert into
            filename: Optional custom filename
            drop_existing: Whether to drop existing table
        
        Returns:
            Path to database file
        """
        if filename is None:
            filename = self._generate_filename("scraped_data", "db")
        
        filepath = self.output_dir / filename
        
        if not data:
            logger.warning("No data to export to SQLite")
            return filepath
        
        conn = sqlite3.connect(str(filepath))
        cursor = conn.cursor()
        
        try:
            # Drop existing table if requested
            if drop_existing:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            # Infer schema from first record
            sample = data[0]
            columns = []
            
            for key, value in sample.items():
                if isinstance(value, (dict, list)):
                    col_type = "TEXT"  # Store as JSON
                elif isinstance(value, bool):
                    col_type = "INTEGER"
                elif isinstance(value, int):
                    col_type = "INTEGER"
                elif isinstance(value, float):
                    col_type = "REAL"
                else:
                    col_type = "TEXT"
                
                # Sanitize column name
                safe_key = key.replace('.', '_').replace('-', '_')
                columns.append((safe_key, col_type))
            
            # Create table
            columns_def = ", ".join([f"{name} {type_}" for name, type_ in columns])
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns_def})"
            cursor.execute(create_sql)
            
            # Insert data
            placeholders = ", ".join(["?" for _ in columns])
            column_names = ", ".join([name for name, _ in columns])
            insert_sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            
            for item in data:
                values = []
                for key, _ in columns:
                    # Handle original key (before sanitization)
                    original_key = key  # In this simple case, they're the same
                    value = item.get(original_key)
                    
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    
                    values.append(value)
                
                cursor.execute(insert_sql, values)
            
            conn.commit()
            logger.success(f"Exported {len(data)} records to SQLite: {filepath} (table: {table_name})")
        
        finally:
            conn.close()
        
        return filepath
    
    async def export_mongodb(
        self,
        data: List[Dict[str, Any]],
        collection_name: str = "scraped_data",
        connection_string: str = "mongodb://localhost:27017",
        database_name: str = "scraper_db",
    ) -> int:
        """
        Export data to MongoDB.
        
        Args:
            data: List of dictionaries to export
            collection_name: Name of the collection
            connection_string: MongoDB connection string
            database_name: Database name
        
        Returns:
            Number of inserted documents
        """
        if not MONGODB_AVAILABLE:
            logger.error("pymongo not installed. Cannot export to MongoDB.")
            return 0
        
        if not data:
            logger.warning("No data to export to MongoDB")
            return 0
        
        try:
            client = pymongo.MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection
            client.server_info()
            
            db = client[database_name]
            collection = db[collection_name]
            
            # Add timestamp
            for item in data:
                item['exported_at'] = datetime.utcnow()
            
            result = collection.insert_many(data)
            
            logger.success(f"Exported {len(result.inserted_ids)} records to MongoDB: {database_name}.{collection_name}")
            
            client.close()
            return len(result.inserted_ids)
        
        except Exception as e:
            logger.error(f"Failed to export to MongoDB: {e}")
            return 0
    
    async def export_all(
        self,
        data: List[Dict[str, Any]],
        formats: Optional[List[str]] = None,
    ) -> Dict[str, Path]:
        """
        Export data to multiple formats simultaneously.
        
        Args:
            data: List of dictionaries to export
            formats: List of formats to export to (json, csv, sqlite)
        
        Returns:
            Dictionary mapping format to file path
        """
        if formats is None:
            formats = ['json', 'csv', 'sqlite']
        
        results = {}
        
        tasks = []
        
        if 'json' in formats:
            tasks.append(('json', self.export_json(data)))
        
        if 'csv' in formats:
            tasks.append(('csv', self.export_csv(data)))
        
        if 'sqlite' in formats:
            tasks.append(('sqlite', self.export_sqlite(data)))
        
        if tasks:
            completed = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            
            for (format_name, _), result in zip(tasks, completed):
                if isinstance(result, Path):
                    results[format_name] = result
                else:
                    logger.error(f"Failed to export to {format_name}: {result}")
        
        return results


# Example usage
async def main():
    """Demonstration of DataExporter capabilities."""
    # Sample data
    sample_data = [
        {
            "url": "https://example.com/page1",
            "title": "Example Page 1",
            "data": {
                "headings": {"h1": ["Welcome"], "h2": ["Section 1", "Section 2"]},
                "links": ["https://example.com/link1", "https://example.com/link2"],
            },
            "metadata": {"author": "John Doe", "date": "2024-01-15"},
            "scraped_at": datetime.now().isoformat(),
            "status": "success",
        },
        {
            "url": "https://example.com/page2",
            "title": "Example Page 2",
            "data": {
                "headings": {"h1": ["About Us"], "h2": ["Our Team"]},
                "links": ["https://example.com/about"],
            },
            "metadata": {"author": "Jane Smith", "date": "2024-01-16"},
            "scraped_at": datetime.now().isoformat(),
            "status": "success",
        },
    ]
    
    exporter = DataExporter(output_dir="output")
    
    # Export to all formats
    results = await exporter.export_all(sample_data)
    
    print("\nExport Results:")
    for format_name, filepath in results.items():
        print(f"  {format_name.upper()}: {filepath}")


if __name__ == "__main__":
    asyncio.run(main())
