import yaml
import logging
from pathlib import Path
from aws_login import AWSLoginManager
from data_processor import DataProcessor
from report_generator import ReportGenerator
from pdf_generator import PDFGenerator
from datetime import datetime

def load_config() -> dict:
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)

def setup_logging(config: dict):
    logging.basicConfig(
        level=config['logging']['level'],
        filename=config['logging']['file'],
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    # Load configuration
    config = load_config()
    setup_logging(config)
    
    try:
        # Initialize components
        aws_login = AWSLoginManager(config)
        data_processor = DataProcessor()
        report_generator = ReportGenerator()
        pdf_generator = PDFGenerator(config)
        
        # Login to AWS
        if not aws_login.login():
            raise Exception("Failed to login to AWS")
        
        # Download CSV
        original_csv = aws_login.download_csv("")
        if not original_csv:
            raise Exception("Failed to download CSV")
            
        # Filter for today's data
        filtered_csv = data_processor.filter_todays_data(original_csv)
        if not filtered_csv:
            raise Exception("Failed to filter today's data")
        
        # Report generation
        analysis = report_generator.generate_report(filtered_csv)
        if not analysis:
            raise Exception("Failed to generate report")
        
        # Generate PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"analysis_report_{timestamp}.pdf"
        output_dir = Path(config['pdf']['output_path'])
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / pdf_filename
        
        if not pdf_generator.generate_report(analysis, str(output_path)):
            raise Exception("Failed to generate PDF report")
        
        logging.info(f"Report generated successfully at {output_path}")
        
        # Cleanup temporary files
        for csv_file in [original_csv, filtered_csv]:
            if Path(csv_file).exists():
                Path(csv_file).unlink()
                logging.info(f"Cleaned up temporary file: {csv_file}")
        
    except Exception as e:
        logging.error(f"Process failed: {str(e)}")
        
    finally:
        aws_login.cleanup()

if __name__ == "__main__":
    main() 