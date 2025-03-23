import pandas as pd
from typing import Dict, Any
import logging
from datetime import datetime
from pathlib import Path

class DataProcessor:
    def __init__(self):
        self.data = None
        
    def load_csv(self, file_path: str) -> bool:
        try:
            self.data = pd.read_csv(file_path)
            return True
        except Exception as e:
            logging.error(f"Failed to load CSV: {str(e)}")
            return False
            
    def preprocess_data(self) -> Dict[str, Any]:
        """Prepare data for AI analysis"""
        if self.data is None:
            return {}
            
        processed_data = {
            'summary': {
                'total_rows': len(self.data),
                'columns': list(self.data.columns)
            },
            'statistics': self.data.describe().to_dict(),
            'sample': self.data.head(5).to_dict()
        }
        
        return processed_data 

    def filter_todays_data(self, input_csv: str) -> str:
        try:
            # Read CSV and filter today's data
            df = pd.read_csv(input_csv)
            df['Start Time'] = pd.to_datetime(df['Start Time'])
            today = datetime.now().strftime('%Y-%m-%d')
            today_data = df[df['Start Time'].dt.strftime('%Y-%m-%d') == today]
            
            # Save filtered data
            filtered_path = Path(input_csv).parent / f"filtered_{Path(input_csv).name}"
            today_data.to_csv(filtered_path, index=False)
            logging.info(f"Created filtered CSV with {len(today_data)} rows")
            
            return str(filtered_path)
            
        except Exception as e:
            logging.error(f"Failed to filter CSV: {str(e)}")
            return None 