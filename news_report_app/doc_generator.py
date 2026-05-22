"""Word document generation with strict Arabic RTL support."""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from models import NewsItem


class DocExporter:
    """Handles Word document generation with Arabic RTL formatting."""
    
    ARABIC_FONTS = ["Traditional Arabic", "Simplified Arabic", "Arial"]
    
    def __init__(self, template_path: Optional[str] = None):
        """Initialize the exporter with optional template path."""
        self.template_path = template_path
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
    
    def _create_default_template(self) -> Document:
        """Create a default document with Arabic header/footer."""
        doc = Document()
        
        # Set default RTL for the document
        section = doc.sections[0]
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.right_margin = Inches(1)
        section.left_margin = Inches(1)
        
        # Add header
        header = section.header
        header_para = header.paragraphs[0]
        header_para.text = "تقرير الأخبار"
        self._apply_rtl_formatting(header_para)
        
        # Add footer
        footer = section.footer
        footer_para = footer.paragraphs[0]
        footer_para.text = f"تم إنشاء التقرير في {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self._apply_rtl_formatting(footer_para)
        
        return doc
    
    def _apply_rtl_formatting(self, paragraph) -> None:
        """Apply strict RTL formatting to a paragraph."""
        paragraph.paragraph_format.bidi = True
        paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        
        for run in paragraph.runs:
            run._element.set(qn('w:rtl'), '1')
            run.font.name = self.ARABIC_FONTS[0]
            run.font.element.rPr.set(qn('w:lang'), 'ar-SA')
    
    def _add_rtl_run(self, paragraph, text: str, **kwargs) -> None:
        """Add a run with RTL formatting to a paragraph."""
        run = paragraph.add_run(text)
        run._element.set(qn('w:rtl'), '1')
        run.font.name = self.ARABIC_FONTS[0]
        
        # Apply optional formatting
        if 'bold' in kwargs:
            run.bold = kwargs['bold']
        if 'italic' in kwargs:
            run.italic = kwargs['italic']
        if 'size' in kwargs:
            run.font.size = Pt(kwargs['size'])
        if 'color' in kwargs:
            run.font.color.rgb = kwargs['color']
        
        # Set language
        rPr = run._element.get_or_add_rPr()
        lang = OxmlElement('w:lang')
        lang.set(qn('w:val'), 'ar-SA')
        rPr.append(lang)
    
    def _add_heading(self, doc: Document, title: str) -> None:
        """Add a news title heading with RTL formatting."""
        para = doc.add_paragraph()
        self._add_rtl_run(para, title, bold=True, size=14)
        para.paragraph_format.space_after = Pt(6)
    
    def _add_source(self, doc: Document, source: str) -> None:
        """Add source line with RTL formatting."""
        para = doc.add_paragraph()
        self._add_rtl_run(para, f"المصدر: {source}", italic=True, size=10, 
                         color=RGBColor(80, 80, 80))
        para.paragraph_format.space_after = Pt(8)
    
    def _add_content(self, doc: Document, content: str) -> None:
        """Add content paragraph with RTL and justified formatting."""
        para = doc.add_paragraph()
        self._add_rtl_run(para, content, size=12)
        para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        para.paragraph_format.space_after = Pt(12)
    
    def _add_image(self, doc: Document, image_path: str) -> bool:
        """Add image with caption, centered and scaled. Returns True if successful."""
        if not image_path:
            return False
        
        if not os.path.exists(image_path):
            print(f"Warning: Image not found: {image_path}")
            return False
        
        try:
            para = doc.add_paragraph()
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            run = para.add_run()
            run.add_picture(image_path, width=Inches(5))
            
            # Add caption
            caption = doc.add_paragraph()
            self._add_rtl_run(caption, "شكل: صورة الخبر", italic=True, size=10)
            caption.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            return True
        except Exception as e:
            print(f"Warning: Could not add image {image_path}: {e}")
            return False
    
    def _add_coordinates(self, doc: Document, coordinates: str) -> None:
        """Add coordinates paragraph with RTL formatting."""
        para = doc.add_paragraph()
        self._add_rtl_run(para, f"📍 {coordinates}", size=11)
        para.paragraph_format.space_after = Pt(8)
    
    def _add_incident_time(self, doc: Document, incident_time: str) -> None:
        """Add incident time paragraph with RTL formatting."""
        para = doc.add_paragraph()
        self._add_rtl_run(para, f"⏰ وقت الحدث: {incident_time}", size=11)
        para.paragraph_format.space_after = Pt(8)
    
    def _add_recommendation(self, doc: Document, recommendation: str) -> None:
        """Add recommendation with special formatting."""
        para = doc.add_paragraph()
        self._add_rtl_run(para, f"💡 {recommendation}", italic=True, size=11)
        
        # Add subtle shading
        shading = OxmlElement('w:shd')
        shading.set(qn('w:val'), 'clear')
        shading.set(qn('w:color'), 'auto')
        shading.set(qn('w:fill'), 'F0F0F0')
        para._element.get_or_add_pPr().append(shading)
        
        para.paragraph_format.space_after = Pt(12)
    
    def generate(self, news_items: List[NewsItem]) -> str:
        """Generate Word document from news items and return file path."""
        # Load or create document
        if self.template_path and os.path.exists(self.template_path):
            doc = Document(self.template_path)
        else:
            doc = self._create_default_template()
        
        # Add each news item
        for i, item in enumerate(news_items):
            # Title
            self._add_heading(doc, item.title)
            
            # Source
            self._add_source(doc, item.source)
            
            # Content
            self._add_content(doc, item.content)
            
            # Image (if exists)
            if item.image_path:
                self._add_image(doc, item.image_path)
            
            # Coordinates (if exists)
            if item.coordinates:
                self._add_coordinates(doc, item.coordinates)
            
            # Incident time (if exists)
            if item.incident_time:
                self._add_incident_time(doc, item.incident_time)
            
            # Recommendation (if exists)
            if item.recommendation:
                self._add_recommendation(doc, item.recommendation)
            
            # Page break between items (except last)
            if i < len(news_items) - 1:
                doc.add_page_break()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"تقرير_الأخبار_{timestamp}.docx"
        filepath = self.output_dir / filename
        
        # Save document
        doc.save(str(filepath))
        
        return str(filepath)