"""Test module for the news report application."""

import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models import NewsItem
from gui import NewsManager
from doc_generator import DocExporter


class TestNewsItem(unittest.TestCase):
    """Test cases for NewsItem model."""

    def test_create_news_item_with_required_fields(self):
        """Test creating a news item with only required fields."""
        item = NewsItem(
            source="وكالة الأنباء",
            title="خبر مهم اليوم",
            content="هذا محتوى الخبر المهم."
        )
        self.assertTrue(item.is_valid())
        self.assertEqual(item.source, "وكالة الأنباء")
        self.assertEqual(item.title, "خبر مهم اليوم")
        self.assertEqual(item.content, "هذا محتوى الخبر المهم.")

    def test_create_news_item_with_all_fields(self):
        """Test creating a news item with all fields."""
        item = NewsItem(
            source="المرصد الإخباري",
            title="تحديث تقنولوجي",
            content="محتوى تفصيلي عن التحديث التقني.",
            image_path="/path/to/image.jpg",
            coordinates="33.5, 36.3",
            incident_time="10:30 صباحاً",
            recommendation="يُنصح بالتحديث الفوري"
        )
        self.assertTrue(item.is_valid())
        self.assertTrue(item.has_attachments())
        self.assertIn("🖼", item.get_attachments_summary())
        self.assertIn("📍", item.get_attachments_summary())
        self.assertIn("⏰", item.get_attachments_summary())
        self.assertIn("💡", item.get_attachments_summary())

    def test_invalid_news_item_missing_source(self):
        """Test that news item without source is invalid."""
        item = NewsItem(
            source="",
            title="عنوان الخبر",
            content="محتوى الخبر"
        )
        self.assertFalse(item.is_valid())

    def test_invalid_news_item_missing_title(self):
        """Test that news item without title is invalid."""
        item = NewsItem(
            source="المصدر",
            title="",
            content="محتوى الخبر"
        )
        self.assertFalse(item.is_valid())

    def test_invalid_news_item_missing_content(self):
        """Test that news item without content is invalid."""
        item = NewsItem(
            source="المصدر",
            title="العنوان",
            content=""
        )
        self.assertFalse(item.is_valid())

    def test_news_item_auto_id(self):
        """Test that news item gets auto-generated ID."""
        item = NewsItem(
            source="المصدر",
            title="العنوان",
            content="المحتوى"
        )
        self.assertIsNotNone(item.id)
        self.assertEqual(len(item.id), 8)

    def test_news_item_auto_timestamp(self):
        """Test that news item gets auto-generated timestamp."""
        before = datetime.now()
        item = NewsItem(
            source="المصدر",
            title="العنوان",
            content="المحتوى"
        )
        after = datetime.now()
        self.assertTrue(before <= item.created_at <= after)

    def test_attachments_summary_no_attachments(self):
        """Test attachments summary when no attachments."""
        item = NewsItem(
            source="المصدر",
            title="العنوان",
            content="المحتوى"
        )
        self.assertEqual(item.get_attachments_summary(), "-")

    def test_attachments_summary_only_image(self):
        """Test attachments summary with only image."""
        item = NewsItem(
            source="المصدر",
            title="العنوان",
            content="المحتوى",
            image_path="/path/to/image.jpg"
        )
        self.assertEqual(item.get_attachments_summary(), "🖼")

    def test_attachments_summary_only_coordinates(self):
        """Test attachments summary with only coordinates."""
        item = NewsItem(
            source="المصدر",
            title="العنوان",
            content="المحتوى",
            coordinates="33.5, 36.3"
        )
        self.assertEqual(item.get_attachments_summary(), "📍")

    def test_attachments_summary_only_recommendation(self):
        """Test attachments summary with only recommendation."""
        item = NewsItem(
            source="المصدر",
            title="العنوان",
            content="المحتوى",
            recommendation="توصية مهمة"
        )
        self.assertEqual(item.get_attachments_summary(), "💡")

    def test_attachments_summary_only_incident_time(self):
        """Test attachments summary with only incident time."""
        item = NewsItem(
            source="المصدر",
            title="العنوان",
            content="المحتوى",
            incident_time="10:30 صباحاً"
        )
        self.assertEqual(item.get_attachments_summary(), "⏰")


class TestNewsManager(unittest.TestCase):
    """Test cases for NewsManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = NewsManager()

    def test_add_item(self):
        """Test adding a news item."""
        item = NewsItem(
            source="المصدر",
            title="العنوان",
            content="المحتوى"
        )
        self.manager.add_item(item)
        self.assertEqual(len(self.manager), 1)

    def test_remove_item(self):
        """Test removing a news item."""
        item1 = NewsItem(source="مصدر 1", title="عنوان 1", content="محتوى 1")
        item2 = NewsItem(source="مصدر 2", title="عنوان 2", content="محتوى 2")
        self.manager.add_item(item1)
        self.manager.add_item(item2)
        
        self.manager.remove_item(0)
        self.assertEqual(len(self.manager), 1)
        self.assertEqual(self.manager.get_item(0).title, "عنوان 2")

    def test_remove_item_out_of_bounds(self):
        """Test removing item with invalid index."""
        item = NewsItem(source="المصدر", title="العنوان", content="المحتوى")
        self.manager.add_item(item)
        
        # Should not raise error
        self.manager.remove_item(100)
        self.assertEqual(len(self.manager), 1)

    def test_get_item(self):
        """Test getting a news item by index."""
        item = NewsItem(source="المصدر", title="العنوان", content="المحتوى")
        self.manager.add_item(item)
        
        retrieved = self.manager.get_item(0)
        self.assertEqual(retrieved.title, "العنوان")

    def test_get_item_out_of_bounds(self):
        """Test getting item with invalid index."""
        result = self.manager.get_item(0)
        self.assertIsNone(result)

    def test_clear(self):
        """Test clearing all news items."""
        for i in range(5):
            item = NewsItem(source=f"مصدر {i}", title=f"عنوان {i}", content=f"محتوى {i}")
            self.manager.add_item(item)
        
        self.assertEqual(len(self.manager), 5)
        self.manager.clear()
        self.assertEqual(len(self.manager), 0)


class TestDocExporter(unittest.TestCase):
    """Test cases for DocExporter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.exporter = DocExporter()

    def test_generate_empty_list(self):
        """Test generating document with empty list."""
        # Should still create a document
        filepath = self.exporter.generate([])
        self.assertTrue(os.path.exists(filepath))
        # Clean up
        os.remove(filepath)

    def test_generate_single_item(self):
        """Test generating document with single news item."""
        item = NewsItem(
            source="الوكالة الإخبارية",
            title="خبر التجربة",
            content="هذا نص تجريبي للخبر للتحقق من عمل المولد."
        )
        filepath = self.exporter.generate([item])
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.docx'))
        # Clean up
        os.remove(filepath)

    def test_generate_multiple_items(self):
        """Test generating document with multiple news items."""
        items = [
            NewsItem(
                source="المصدر الأول",
                title="الخبر الأول",
                content="محتوى الخبر الأول"
            ),
            NewsItem(
                source="المصدر الثاني",
                title="الخبر الثاني",
                content="محتوى الخبر الثاني"
            ),
            NewsItem(
                source="المصدر الثالث",
                title="الخبر الثالث",
                content="محتوى الخبر الثالث"
            )
        ]
        filepath = self.exporter.generate(items)
        self.assertTrue(os.path.exists(filepath))
        # Clean up
        os.remove(filepath)

    def test_generate_with_attachments(self):
        """Test generating document with news items that have attachments."""
        item = NewsItem(
            source="المصدر",
            title="خبر مع مرفقات",
            content="محتوى الخبر",
            coordinates="33.5, 36.3",
            recommendation="توصية مهمة"
        )
        filepath = self.exporter.generate([item])
        self.assertTrue(os.path.exists(filepath))
        # Clean up
        os.remove(filepath)

    def test_generate_with_incident_time(self):
        """Test generating document with news items that have incident time."""
        item = NewsItem(
            source="المصدر",
            title="خبر بوقت حادث",
            content="محتوى الخبر",
            incident_time="10:30 صباحاً"
        )
        filepath = self.exporter.generate([item])
        self.assertTrue(os.path.exists(filepath))
        # Clean up
        os.remove(filepath)


def create_sample_test_news() -> list:
    """Create sample test news items for manual testing.
    
    Returns:
        List of NewsItem objects for testing.
    """
    return [
        NewsItem(
            source="المرصد الإخباري",
            title="إطلاق منصة جديدة للذكاء الاصطناعي",
            content="أعلنت شركة التكنولوجيا اليوم عن إطلاق منصة جديدة للذكاء الاصطناعي تهدف إلى تحسين تجربة المستخدم في التطبيقات اليومية. تم تصميم المنصة لتكون سهلة الاستخدام وفعّالة من حيث التكلفة.",
            coordinates="33.5138, 36.2765",
            incident_time="09:00 صباحاً",
            recommendation="يُنصح بالاطلاع على التحديثات الأمنية قبل الاستخدام"
        ),
        NewsItem(
            source="وكالة الأنباء الوطنية",
            title="زيادة في أسعار الطاقة اليوم",
            content="أعلنت وزارة الطاقة عن زيادة مؤقتة في أسعار الطاقة اعتباراً من الشهر المقبل، وذلك بسبب ارتفاع أسعار الوقود في الأسواق العالمية.",
            incident_time="14:30 مساءً",
            recommendation="يُنصح المواطنون باتخاذ إجراءات لتقليل استهلاك الطاقة"
        ),
        NewsItem(
            source="صحيفة الصباح",
            title="مبادرة شبابية للتطوع المجتمعي",
            content="بدأت مبادرة جديدة تجمع الشباب للقيام بالأعمال التطوعية في المجتمعات المحلية، تشمل تنظيف الحدائق العامة وتوعية المواطنين حول أهمية الحفاظ على البيئة.",
            coordinates="33.5, 36.3"
        ),
        NewsItem(
            source="النهار",
            title="افتتاح مركز ثقافي جديد",
            content="تم افتتاح مركز ثقافي متكامل في اللاذقية يضم مكتبة عامة وقاعات عرض فنية وورش عمل متخصصة. المركز يفتح أبوابه للجميع دون تكلفة.",
            incident_time="08:00 صباحاً",
            recommendation="يُنصح بزيارة المركز للاستفادة من البرامج الثقافية المتنوعة"
        ),
        NewsItem(
            source="رواد التقنية",
            title="تحديثات أمان جديدة للتطبيقات",
            content="صدرت تحديثات أمان مهمة للتطبيقات الشائعة لحماية المستخدمين من الهجمات الإلكترونية. يُنصح بتحديث جميع التطبيقات فوراً.",
            coordinates="33.5138, 36.2765",
            incident_time="12:00 ظهراً",
            recommendation="قم بتحديث جميع تطبيقاتك فوراً لضمان الأمان"
        )
    ]


def run_manual_test():
    """Run a manual test to generate a sample document."""
    print("=" * 50)
    print("Running manual test to generate sample document")
    print("=" * 50)
    
    # Create sample news
    news_items = create_sample_test_news()
    
    # Create exporter and generate document
    exporter = DocExporter()
    filepath = exporter.generate(news_items)
    
    print("\nTest document generated successfully!")
    # Write to stdout buffer to handle unicode
    sys.stdout.buffer.write(f"File path: {filepath}\n".encode('utf-8'))
    print("Number of news items:", len(news_items))
    
    return filepath


if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run manual test
    print("\n")
    run_manual_test()