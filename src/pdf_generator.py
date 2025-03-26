from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
import logging
from typing import Dict, Any
from datetime import datetime

class PDFGenerator:
    def __init__(self, config: dict):
        self.config = config
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Set up custom styles for the PDF"""
        self.styles.add(ParagraphStyle(
            'ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0066CC'),
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            'DateStyle',
            parent=self.styles['Normal'],
            fontSize=14, 
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2C3E50'), 
            spaceAfter=25,  
            fontName='Helvetica-Bold'  
        ))
        
        # Section Headers with modern look
        self.styles.add(ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=15,
            textColor=colors.HexColor('#2C3E50'),
            fontName='Helvetica-Bold',
            borderColor=colors.HexColor('#0066CC'),
            borderWidth=1,
            borderPadding=5
        ))

        # Table cell style
        self.styles.add(ParagraphStyle(
            'TableCell',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2C3E50')
        ))
        
        # Define modern table style
        self.table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2C3E50')),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#EEEEEE')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F9F9F9'), colors.white]),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
        ])

    def _parse_sections(self, lines: list) -> dict:
        """Parse report content into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line == 'Scheduler Run Analysis Report':
                sections['title'] = line
            elif line.startswith('Date:'):
                sections['date'] = line
            elif not line.startswith(' ') and not ':' in line:
                if current_section:
                    sections[current_section] = current_content
                current_section = line
                current_content = []
            else:
                current_content.append(line)
                
        if current_section:
            sections[current_section] = current_content
            
        return sections

    def generate_report(self, analysis: dict, output_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                topMargin=50,
                bottomMargin=50,
                leftMargin=40,
                rightMargin=40
            )
            
            story = []
            
            if not analysis or 'content' not in analysis:
                raise ValueError("Invalid analysis data")
                
            lines = analysis['content'].split('\n')
            sections = self._parse_sections(lines)
            
            if 'title' not in sections:
                raise ValueError("Report title not found")
                
            story.append(Paragraph(sections['title'], self.styles['ReportTitle']))
            story.append(Paragraph(sections['date'], self.styles['DateStyle']))
            
            # Add each section
            for section_name, section_data in sections.items():
                if section_name not in ['title', 'date']:
                    story.append(Paragraph(section_name, self.styles['SectionHeader']))
                    
                    # All sections use key-value table format
                    data = [['Metric', 'Value']]
                    for item in section_data:
                        if ':' in item:
                            metric, value = item.split(':', 1)
                            data.append([metric.strip(), value.strip()])
                    
                    if len(data) > 1:
                        # Apply the same styling for all sections
                        table = Table(data, colWidths=[280, 200])
                        table.setStyle(self.table_style)
                        story.append(table)
                    
                    story.append(Spacer(1, 20))
            
            doc.build(story)
            return True
            
        except Exception as e:
            logging.error(f"PDF generation failed: {str(e)}")
            return False

    def _add_section(self, story: list, title: str, content: list):
        """Add a section with hierarchical bullet points"""
        story.append(Paragraph(title, self.styles['SectionTitle']))
        
        for item in content:
            # Check if it's a sub-bullet point (starts with ◦)
            if item.startswith('◦'):
                story.append(Paragraph(f"◦ {item[1:].strip()}", self.styles['SubBulletPoint']))
            # Check if it's a deeper sub-bullet point (starts with ▪)
            elif item.startswith('▪'):
                story.append(Paragraph(f"▪ {item[1:].strip()}", 
                           ParagraphStyle('DeepBullet', parent=self.styles['SubBulletPoint'], leftIndent=60)))
            # Regular bullet point
            else:
                story.append(Paragraph(f"• {item.strip()}", self.styles['BulletPoint']))
        
        story.append(Spacer(1, 12)) 