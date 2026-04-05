import psycopg2
import json
import sys
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def update_all_channel_names():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='antigravity',
            user='n8n',
            password='n8n'
        )
        cur = conn.cursor()
        
        cur.execute("SELECT id, credentials_data FROM platform_credentials WHERE platform = 'youtube' AND (account_name IS NULL OR account_name = 'YouTube Channel' OR account_name = 'Cuenta Conectada')")
        rows = cur.fetchall()
        
        print(f"Found {len(rows)} accounts to update.")
        
        for row in rows:
            record_id, data = row
            try:
                creds = Credentials(
                    token=data.get('access_token'),
                    refresh_token=data.get('refresh_token'),
                    token_uri=data.get('token_uri'),
                    client_id=data.get('client_id'),
                    client_secret=data.get('client_secret'),
                    scopes=data.get('scopes')
                )
                
                youtube = build('youtube', 'v3', credentials=creds)
                channels_response = youtube.channels().list(
                    part='snippet',
                    mine=True
                ).execute()
                
                if channels_response.get('items'):
                    name = channels_response['items'][0]['snippet']['title']
                    print(f"Updating ID {record_id} with name: {name}")
                    cur.execute("UPDATE platform_credentials SET account_name = %s WHERE id = %s", (name, record_id))
                else:
                    print(f"No channel found for record {record_id}")
            except Exception as e:
                print(f"Error updating record {record_id}: {e}")
                
        conn.commit()
        cur.close()
        conn.close()
        print("Done.")
    except Exception as e:
        print(f"Global Error: {e}")

if __name__ == "__main__":
    update_all_channel_names()
