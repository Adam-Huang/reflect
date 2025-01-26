import json
import sqlite3
from datetime import datetime

def migrate_data():
    """Migrate data from JSON files to SQLite database"""
    # Connect to SQLite database
    conn = sqlite3.connect('./data/memory.db')
    cursor = conn.cursor()
    
    # Load data from JSON files
    with open('./data/memory_state.json', 'r') as f:
        memory_data = json.load(f)['memory_data']
    
    with open('./data/labels.json', 'r') as f:
        labels = json.load(f)
    
    with open('./data/triggers.json', 'r') as f:
        triggers = json.load(f)
    
    # Insert labels with default descriptions
    for label in labels:
        if label:  # Skip empty labels
            cursor.execute('''
            INSERT OR REPLACE INTO Labels (label, description)
            VALUES (?, ?)
            ''', (label, f"Label for categorizing memories as '{label}'"))
    
    # Insert triggers with default descriptions
    for trigger in triggers:
        if trigger:  # Skip empty triggers
            cursor.execute('''
            INSERT OR REPLACE INTO Triggers (trigger, description)
            VALUES (?, ?)
            ''', (trigger, f"Trigger for activating memories related to '{trigger}'"))
    
    # Insert memories with comma-separated labels
    for memory in memory_data:
        # Convert datetime strings to datetime objects
        created_at = datetime.fromisoformat(memory['created_at'])
        updated_at = datetime.fromisoformat(memory['updated_at'])
        
        # Join labels with commas
        labels = ','.join(filter(None, memory['labels']))  # filter out empty labels
        
        # Insert memory
        cursor.execute('''
        INSERT OR REPLACE INTO Memory 
        (original_text, summary, created_at, updated_at, labels, trigger, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory['original_text'],
            memory['summary'],
            created_at,
            updated_at,
            labels,
            memory['trigger'],
            # Store embedding as bytes if it exists
            bytes(str(memory['embedding']), 'utf-8') if memory['embedding'] else None
        ))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    migrate_data()
    print("Migration completed successfully!")
