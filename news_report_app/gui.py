"""Modern GUI application for news report generation with CustomTkinter."""

import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import customtkinter as ctk
from PIL import Image, ImageTk
import pyperclip
import arabic_reshaper

from models import NewsItem
from doc_generator import DocExporter

def fix_arabic_text(text):
    """Return text as-is for Arabic display in RTL GUI."""
    return text

# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Color palette
COLORS = {
    "primary": "#4CAF50",
    "primary_hover": "#45A049",
    "secondary": "#2196F3",
    "secondary_hover": "#1976D2",
    "danger": "#F44336",
    "danger_hover": "#D32F2F",
    "warning": "#FF9800",
    "success": "#4CAF50",
    "bg_dark": "#1a1a1a",
    "bg_card": "#2a2a2a",
    "text_primary": "#ffffff",
    "text_secondary": "#b0b0b0",
}


class NewsManager:
    """Manages the collection of news items."""
    
    def __init__(self):
        self.items: List[NewsItem] = []
        self.sources: List[str] = []
        self.categories: List[str] = []
        self.data_file = Path(__file__).parent / "output" / "news_data.json"
        self._load()
    
    def _load(self):
        """Load news items from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Clear existing items to prevent duplication
                    self.items.clear()
                    self.sources.clear()
                    self.categories.clear()
                    for item_data in data.get('items', []):
                        item = NewsItem(
                            id=item_data.get('id', ''),
                            source=item_data.get('source', ''),
                            title=item_data.get('title', ''),
                            content=item_data.get('content', ''),
                            category=item_data.get('category', ''),
                            image_path=item_data.get('image_path'),
                            coordinates=item_data.get('coordinates'),
                            incident_time=item_data.get('incident_time'),
                            recommendation=item_data.get('recommendation'),
                            created_at=datetime.fromisoformat(item_data.get('created_at', datetime.now().isoformat())),
                            selected_for_report=item_data.get('selected_for_report', True)
                        )
                        self.items.append(item)
                        if item.source and item.source not in self.sources:
                            self.sources.append(item.source)
                        if item.category and item.category not in self.categories:
                            self.categories.append(item.category)
            except Exception as e:
                print(f"Warning: Could not load saved data: {e}")
    
    def _save(self):
        """Save news items to file."""
        self.data_file.parent.mkdir(exist_ok=True)
        data = {
            'items': [
                {
                    'id': item.id,
                    'source': item.source,
                    'title': item.title,
                    'content': item.content,
                    'category': item.category,
                    'image_path': item.image_path,
                    'coordinates': item.coordinates,
                    'incident_time': item.incident_time,
                    'recommendation': item.recommendation,
                    'created_at': item.created_at.isoformat(),
                    'selected_for_report': item.selected_for_report
                }
                for item in self.items
            ]
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_item(self, item: NewsItem) -> None:
        """Add a news item to the collection."""
        self.items.append(item)
        if item.source and item.source not in self.sources:
            self.sources.append(item.source)
        if item.category and item.category not in self.categories:
            self.categories.append(item.category)
        self._save()
    
    def remove_item(self, index: int) -> None:
        """Remove a news item by index."""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self._save()
    
    def get_item(self, index: int) -> Optional[NewsItem]:
        """Get a news item by index."""
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def clear(self) -> None:
        """Clear all news items."""
        self.items.clear()
        self._save()
    
    def toggle_selection(self, index: int) -> None:
        """Toggle selection status of a news item."""
        if 0 <= index < len(self.items):
            self.items[index].selected_for_report = not self.items[index].selected_for_report
            self._save()
    
    def select_all(self) -> None:
        """Select all news items."""
        for item in self.items:
            item.selected_for_report = True
        self._save()
    
    def deselect_all(self) -> None:
        """Deselect all news items."""
        for item in self.items:
            item.selected_for_report = False
        self._save()
    
    def get_selected_items(self) -> List[NewsItem]:
        """Get only selected news items."""
        return [item for item in self.items if item.selected_for_report]
    
    def __len__(self) -> int:
        return len(self.items)


class NewsDialog(ctk.CTkToplevel):
    """Modal dialog for adding/editing news items with modern UI."""
    
    def __init__(self, parent, on_save_callback, sources: List[str] = None, categories: List[str] = None):
        super().__init__(parent)
        self.parent = parent
        self.on_save = on_save_callback
        self.available_sources = sources or []
        self.available_categories = categories or []
        
        self.title("✨ إضافة خبر جديد")
        self.geometry("750x950")
        self.resizable(True, True)
        self.minsize(650, 850)
        self.transient(parent)
        self.grab_set()
        
        self.image_path: Optional[str] = None
        self.image_preview = None
        
        self._create_widgets()
        self._center_window()
    
    def _center_window(self):
        """Center the dialog on parent window."""
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (750 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (950 // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create all dialog widgets with modern styling."""
        # Main scrollable frame
        main_scroll = ctk.CTkScrollableFrame(self, label_text=fix_arabic_text("معلومات الخبر"))
        main_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header section
        header_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="📝 إضافة خبر جديد",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["primary"]
        )
        title_label.pack(side="right")
        
        # Source field
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        source_label = ctk.CTkLabel(
            field_frame, 
            text="📰 المصدر *", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        source_label.pack(anchor="e", pady=(0, 5))
        
        self.source_var = tk.StringVar()
        self.source_combo = ctk.CTkComboBox(
            field_frame,
            values=self.available_sources + ["--- مصدر جديد ---"],
            variable=self.source_var,
            width=650,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13)
        )
        self.source_combo.pack(fill="x", anchor="e")
        self.source_combo.set("")
        self.source_combo.bind("<<ComboboxSelected>>", self._on_source_selected)
        
        # Category field
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        category_label = ctk.CTkLabel(
            field_frame, 
            text="📋 تصنيف الخبر", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        category_label.pack(anchor="e", pady=(0, 5))
        
        self.category_var = tk.StringVar()
        default_categories = ["عام", "سياسة", "اقتصاد", "رياضة", "تكنولوجيا", "صحة", "تعليم", "ثقافة", "منوعات", "حوادث", "طقس"]
        all_categories = list(dict.fromkeys(self.available_categories + default_categories))
        self.category_combo = ctk.CTkComboBox(
            field_frame,
            values=all_categories,
            variable=self.category_var,
            width=650,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=13)
        )
        self.category_combo.pack(fill="x", anchor="e")
        self.category_combo.set("")
        
        # Title field
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            field_frame, 
            text="🏷️ العنوان *", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        title_label.pack(anchor="e", pady=(0, 5))
        
        self.title_var = tk.StringVar()
        self.title_entry = ctk.CTkEntry(
            field_frame, 
            textvariable=self.title_var, 
            width=650, 
            font=ctk.CTkFont(size=13),
            placeholder_text="أدخل عنوان الخبر هنا..."
        )
        self.title_entry.pack(fill="x", anchor="e")
        
        # Content field
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        content_label = ctk.CTkLabel(
            field_frame, 
            text="📝 المحتوى *", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        content_label.pack(anchor="e", pady=(0, 5))
        
        self.content_text = ctk.CTkTextbox(
            field_frame, 
            height=200, 
            width=650, 
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.content_text.pack(fill="x", anchor="e")
        self.content_text.bind("<Control-v>", self._on_paste)
        self.content_text.bind("<Control-V>", self._on_paste)
        
        # Image section
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        image_label = ctk.CTkLabel(
            field_frame, 
            text="📷 الصورة المرفقة", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        image_label.pack(anchor="e", pady=(0, 5))
        
        img_container = ctk.CTkFrame(field_frame)
        img_container.pack(fill="x", anchor="e")
        
        btn_frame = ctk.CTkFrame(img_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="📁 اختيار صورة", 
            command=self._select_image,
            font=ctk.CTkFont(size=13),
            width=150,
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"]
        ).pack(side="right", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame, 
            text="🗑️ إزالة", 
            command=self._remove_image,
            font=ctk.CTkFont(size=13),
            width=100,
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"]
        ).pack(side="right")
        
        self.image_info_label = ctk.CTkLabel(
            img_container, 
            text="لم يتم اختيار صورة", 
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        self.image_info_label.pack(anchor="e", pady=(0, 10))
        
        # Image preview
        self.preview_frame = ctk.CTkFrame(img_container, fg_color=COLORS["bg_card"])
        self.preview_frame.pack(fill="x", pady=(0, 10))
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.preview_label.pack(pady=20)
        
        # Coordinates
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        coords_label = ctk.CTkLabel(
            field_frame, 
            text="📍 الإحداثيات/الموقع", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        coords_label.pack(anchor="e", pady=(0, 5))
        
        self.coords_var = tk.StringVar()
        self.coords_entry = ctk.CTkEntry(
            field_frame, 
            textvariable=self.coords_var, 
            width=650, 
            font=ctk.CTkFont(size=13),
            placeholder_text="مثال: 24.7136° N, 46.6753° E"
        )
        self.coords_entry.pack(fill="x", anchor="e")
        
        # Incident Time
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        time_label = ctk.CTkLabel(
            field_frame, 
            text="⏰ وقت الحدث", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        time_label.pack(anchor="e", pady=(0, 5))
        
        self.time_var = tk.StringVar()
        self.time_entry = ctk.CTkEntry(
            field_frame, 
            textvariable=self.time_var, 
            width=650, 
            font=ctk.CTkFont(size=13),
            placeholder_text="مثال: 2024-01-15 14:30"
        )
        self.time_entry.pack(fill="x", anchor="e")
        
        # Recommendation
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        rec_label = ctk.CTkLabel(
            field_frame, 
            text="💡 توصية أو ملاحظة", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        rec_label.pack(anchor="e", pady=(0, 5))
        
        self.rec_text = ctk.CTkTextbox(
            field_frame, 
            height=120, 
            width=650, 
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.rec_text.pack(fill="x", anchor="e")
        self.rec_text.bind("<Control-v>", self._on_paste)
        self.rec_text.bind("<Control-V>", self._on_paste)
        
        # Button frame at bottom
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            button_frame, 
            text="✅ حفظ الخبر", 
            command=self._save,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            width=200,
            height=50
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame, 
            text="❌ إلغاء", 
            command=self.destroy,
            font=ctk.CTkFont(size=15),
            fg_color="#757575",
            hover_color="#616161",
            width=150,
            height=50
        ).pack(side="left")
    
    def _on_source_selected(self, event=None):
        """Handle selection of 'New Source' option."""
        if self.source_var.get() == "--- مصدر جديد ---":
            self.source_combo.set("")
            self.source_combo.focus()
    
    def _select_image(self):
        """Open file dialog to select an image and show preview."""
        file_path = filedialog.askopenfilename(
            title="اختر صورة",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image_path = file_path
            filename = os.path.basename(file_path)
            filesize = os.path.getsize(file_path) / 1024
            
            self.image_info_label.configure(
                text=f"📄 {filename} ({filesize:.1f} KB)",
                text_color=COLORS["success"]
            )
            
            try:
                img = Image.open(file_path)
                img.thumbnail((400, 250), Image.Resampling.LANCZOS)
                self.image_preview = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=img.size
                )
                self.preview_label.configure(image=self.image_preview, text="")
            except Exception as e:
                self.preview_label.configure(text=f"⚠️ خطأ في المعاينة: {str(e)}")
    
    def _remove_image(self):
        """Remove selected image."""
        self.image_path = None
        self.image_preview = None
        self.image_info_label.configure(
            text="لم يتم اختيار صورة",
            text_color=COLORS["text_secondary"]
        )
        self.preview_label.configure(image=None, text="")
    
    def _on_paste(self, event):
        """Handle paste operation using pyperclip."""
        try:
            clipboard_text = pyperclip.paste()
            widget = event.widget
            widget.insert("insert", clipboard_text)
            return "break"
        except Exception:
            return None
    
    def _save(self):
        """Validate and save the news item."""
        source = self.source_var.get().strip()
        title = self.title_var.get().strip()
        content = self.content_text.get("1.0", "end").strip()
        
        if not source or source == "--- مصدر جديد ---":
            messagebox.showerror("خطأ", "يرجى إدخال المصدر", parent=self)
            return
        
        if not title:
            messagebox.showerror("خطأ", "يرجى إدخال العنوان", parent=self)
            return
        
        if not content:
            messagebox.showerror("خطأ", "يرجى إدخال المحتوى", parent=self)
            return
        
        category = self.category_var.get().strip() or "عام"
        coordinates = self.coords_var.get().strip()
        incident_time = self.time_var.get().strip()
        recommendation = self.rec_text.get("1.0", "end").strip()
        
        new_item = NewsItem(
            source=source,
            title=title,
            content=content,
            category=category,
            image_path=self.image_path,
            coordinates=coordinates,
            incident_time=incident_time,
            recommendation=recommendation
        )
        
        self.on_save(new_item)
        self.destroy()


class ModernNewsApp(ctk.CTk):
    """Modern news management application with checkbox selection."""
    
    def __init__(self):
        super().__init__()
        
        self.title("📰 نظام إدارة الأخبار الحديث")
        self.geometry("1400x900")
        self.minsize(1200, 800)
        
        self.news_manager = NewsManager()
        self.current_filter = ""
        self.current_category_filter = "الكل"
        
        self._setup_ui()
        self._load_news()
    
    def _setup_ui(self):
        """Setup the modern user interface."""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Sidebar
        self._create_sidebar()
        
        # Main content area
        self._create_main_area()
    
    def _create_sidebar(self):
        """Create the sidebar with statistics and actions."""
        sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="ns")
        sidebar.grid_propagate(False)
        
        # Logo/Title
        title_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=30)
        
        logo_label = ctk.CTkLabel(
            title_frame,
            text="📰",
            font=ctk.CTkFont(size=40)
        )
        logo_label.pack()
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=fix_arabic_text("نظام إدارة الأخبار"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title_label.pack(pady=(10, 5))
        
        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Modern News Manager",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        subtitle_label.pack()
        
        # Statistics card
        stats_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"], corner_radius=15)
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        stats_title = ctk.CTkLabel(
            stats_frame,
            text=fix_arabic_text("📊 الإحصائيات"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        stats_title.pack(pady=(15, 10))
        
        self.total_label = ctk.CTkLabel(
            stats_frame,
            text=fix_arabic_text("إجمالي الأخبار: 0"),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.total_label.pack(pady=5)
        
        self.selected_label = ctk.CTkLabel(
            stats_frame,
            text=fix_arabic_text("المحددة للتقرير: 0"),
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        )
        self.selected_label.pack(pady=5)
        
        # Quick actions
        actions_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            actions_frame,
            text=fix_arabic_text("➕ إضافة خبر جديد"),
            command=self._add_news,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=45,
            corner_radius=10
        ).pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(
            actions_frame,
            text=fix_arabic_text("📄 توليد التقرير Word"),
            command=self._generate_report,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            height=45,
            corner_radius=10
        ).pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(
            actions_frame,
            text=fix_arabic_text("🔄 تحديث القائمة"),
            command=self._load_news,
            font=ctk.CTkFont(size=14),
            fg_color="#757575",
            hover_color="#616161",
            height=40,
            corner_radius=10
        ).pack(fill="x")
        
        # Filters
        filter_frame = ctk.CTkFrame(sidebar, fg_color=COLORS["bg_card"], corner_radius=15)
        filter_frame.pack(fill="x", padx=20, pady=20)
        
        filter_title = ctk.CTkLabel(
            filter_frame,
            text=fix_arabic_text("🔍 الفلاتر"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        filter_title.pack(pady=(15, 10))
        
        # Search box
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._filter_news)
        search_entry = ctk.CTkEntry(
            filter_frame,
            textvariable=self.search_var,
            placeholder_text=fix_arabic_text("بحث بالعنوان أو المصدر..."),
            font=ctk.CTkFont(size=13),
            height=40,
            corner_radius=10
        )
        search_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Category filter
        cat_label = ctk.CTkLabel(
            filter_frame,
            text=fix_arabic_text("تصفية حسب التصنيف:"),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        cat_label.pack(anchor="e", padx=15)
        
        categories = ["الكل", "عام", "سياسة", "اقتصاد", "رياضة", "تكنولوجيا", "صحة", "تعليم", "ثقافة", "منوعات", "حوادث", "طقس"]
        self.category_filter_var = tk.StringVar(value="الكل")
        self.category_filter_var.trace("w", self._filter_news)
        
        category_combo = ctk.CTkComboBox(
            filter_frame,
            values=categories,
            variable=self.category_filter_var,
            font=ctk.CTkFont(size=13),
            height=35,
            corner_radius=10,
            state="readonly"
        )
        category_combo.pack(fill="x", padx=15, pady=(5, 15))
        
        # Selection controls
        select_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        select_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            select_frame,
            text=fix_arabic_text("✓ تحديد الكل"),
            command=self._select_all,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["success"],
            hover_color="#45A049",
            height=35,
            corner_radius=8
        ).pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(
            select_frame,
            text=fix_arabic_text("✗ إلغاء تحديد الكل"),
            command=self._deselect_all,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["warning"],
            hover_color="#F57C00",
            height=35,
            corner_radius=8
        ).pack(fill="x")
    
    def _create_main_area(self):
        """Create the main content area with news table."""
        main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        main_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_card"], corner_radius=15, height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        header_label = ctk.CTkLabel(
            header_frame,
            text=fix_arabic_text("📋 قائمة الأخبار"),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        header_label.pack(side="right", padx=30, pady=20)
        
        # Info label
        self.info_label = ctk.CTkLabel(
            header_frame,
            text=fix_arabic_text("انقر نقرًا مزدوجًا على أي صف لتبديل التحديد"),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.info_label.pack(side="right", padx=30, pady=(35, 10))
        
        # Scrollable frame for news items
        self.news_scroll = ctk.CTkScrollableFrame(main_frame, corner_radius=15)
        self.news_scroll.pack(fill="both", expand=True)
        
        # Create treeview-like structure with checkboxes
        self._create_news_cards()
    
    def _create_news_cards(self):
        """Create card-based layout for news items with checkboxes."""
        # Clear existing cards
        for widget in self.news_scroll.winfo_children():
            widget.destroy()
        
        filtered_items = self._get_filtered_items()
        
        if not filtered_items:
            empty_label = ctk.CTkLabel(
                self.news_scroll,
                text=fix_arabic_text("لا توجد أخبار لعرضها"),
                font=ctk.CTkFont(size=16),
                text_color=COLORS["text_secondary"]
            )
            empty_label.pack(pady=50)
            return
        
        # Display news as cards
        for idx, item in enumerate(filtered_items):
            self._create_news_card(item, idx)
    
    def _create_news_card(self, item, display_idx):
        """Create a single news card with checkbox."""
        actual_idx = self.news_manager.items.index(item)
        
        card = ctk.CTkFrame(self.news_scroll, fg_color=COLORS["bg_card"], corner_radius=12)
        card.pack(fill="x", padx=15, pady=10)
        
        # Top row: Checkbox, Category badge, Title
        top_frame = ctk.CTkFrame(card, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=15)
        
        # Checkbox
        checkbox_var = tk.BooleanVar(value=item.selected_for_report)
        checkbox = ctk.CTkCheckBox(
            top_frame,
            text="",
            variable=checkbox_var,
            command=lambda idx=actual_idx: self._toggle_selection(idx),
            width=30,
            height=30,
            corner_radius=8
        )
        checkbox.pack(side="left", padx=(0, 15))
        
        # Category badge
        category_colors = {
            "سياسة": "#E53935",
            "اقتصاد": "#FB8C00",
            "رياضة": "#43A047",
            "تكنولوجيا": "#1E88E5",
            "صحة": "#00ACC1",
            "تعليم": "#8E24AA",
            "ثقافة": "#D81B60",
            "حوادث": "#F4511E",
            "طقس": "#00BCD4",
            "منوعات": "#7CB342",
            "عام": "#757575"
        }
        cat_color = category_colors.get(item.category, "#757575")
        
        cat_badge = ctk.CTkLabel(
            top_frame,
            text=f"📋 {fix_arabic_text(item.category)}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="white",
            fg_color=cat_color,
            corner_radius=8,
            padx=15,
            pady=5
        )
        cat_badge.pack(side="right")
        
        # Title
        title_label = ctk.CTkLabel(
            top_frame,
            text=fix_arabic_text(item.title[:80] + "..." if len(item.title) > 80 else item.title),
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        )
        title_label.pack(side="right", padx=15, fill="x", expand=True)
        
        # Middle row: Source, Date, Image indicator
        mid_frame = ctk.CTkFrame(card, fg_color="transparent")
        mid_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        source_label = ctk.CTkLabel(
            mid_frame,
            text=f"📰 {fix_arabic_text(item.source)}",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["secondary"]
        )
        source_label.pack(side="right", padx=(0, 20))
        
        date_label = ctk.CTkLabel(
            mid_frame,
            text=f"📅 {item.created_at.strftime('%Y-%m-%d %H:%M')}",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        date_label.pack(side="right", padx=20)
        
        if item.image_path:
            img_indicator = ctk.CTkLabel(
                mid_frame,
                text=fix_arabic_text("🖼️ صورة مرفقة"),
                font=ctk.CTkFont(size=11),
                text_color=COLORS["success"]
            )
            img_indicator.pack(side="right", padx=20)
        
        # Bottom row: Content preview
        content_preview = item.content[:150] + "..." if len(item.content) > 150 else item.content
        content_label = ctk.CTkLabel(
            card,
            text=fix_arabic_text(content_preview),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="e",
            justify="right",
            wraplength=900
        )
        content_label.pack(fill="x", padx=15, pady=(0, 15))
        
        # Action buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkButton(
            btn_frame,
            text=fix_arabic_text("👁️ عرض"),
            command=lambda idx=actual_idx: self._view_news(idx),
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            width=100,
            height=32,
            corner_radius=8
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text=fix_arabic_text("✏️ تعديل"),
            command=lambda idx=actual_idx: self._edit_news(idx),
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["warning"],
            hover_color="#F57C00",
            width=100,
            height=32,
            corner_radius=8
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text=fix_arabic_text("🗑️ حذف"),
            command=lambda idx=actual_idx: self._delete_news(idx),
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            width=100,
            height=32,
            corner_radius=8
        ).pack(side="left")
        
        # Bind double-click to toggle selection
        card.bind("<Double-Button-1>", lambda e, idx=actual_idx: self._toggle_selection(idx))
        for child in card.winfo_children():
            if isinstance(child, (ctk.CTkLabel, ctk.CTkFrame)):
                child.bind("<Double-Button-1>", lambda e, idx=actual_idx: self._toggle_selection(idx))
    
    def _get_filtered_items(self):
        """Get filtered news items based on search and category."""
        items = self.news_manager.items
        
        # Apply category filter
        if self.category_filter_var.get() != "الكل":
            items = [item for item in items if item.category == self.category_filter_var.get()]
        
        # Apply search filter
        search_term = self.search_var.get().lower()
        if search_term:
            items = [
                item for item in items
                if search_term in item.title.lower() or search_term in item.source.lower()
            ]
        
        return items
    
    def _filter_news(self, *args):
        """Refresh news list with current filters."""
        self._create_news_cards()
        self._update_stats()
    
    def _update_stats(self):
        """Update statistics labels."""
        total = len(self.news_manager.items)
        selected = len(self.news_manager.get_selected_items())
        
        self.total_label.configure(text=f"إجمالي الأخبار: {total}")
        self.selected_label.configure(text=f"المحددة للتقرير: {selected}")
    
    def _load_news(self):
        """Load and display news items."""
        self.news_manager._load()
        self._create_news_cards()
        self._update_stats()
    
    def _add_news(self):
        """Open dialog to add new news."""
        dialog = NewsDialog(self, self._on_news_saved, self.news_manager.sources, self.news_manager.categories)
        self.wait_window(dialog)
    
    def _on_news_saved(self, item: NewsItem):
        """Handle saved news item."""
        self.news_manager.add_item(item)
        self._load_news()
        messagebox.showinfo("نجاح", "تم إضافة الخبر بنجاح!")
    
    def _toggle_selection(self, index):
        """Toggle selection status of a news item."""
        self.news_manager.toggle_selection(index)
        self._create_news_cards()
        self._update_stats()
    
    def _select_all(self):
        """Select all news items."""
        self.news_manager.select_all()
        self._create_news_cards()
        self._update_stats()
    
    def _deselect_all(self):
        """Deselect all news items."""
        self.news_manager.deselect_all()
        self._create_news_cards()
        self._update_stats()
    
    def _view_news(self, index):
        """View news details."""
        item = self.news_manager.get_item(index)
        if item:
            details = f"""
العنوان: {item.title}
المصدر: {item.source}
التصنيف: {item.category}
المحتوى: {item.content[:300]}...

الإحداثيات: {item.coordinates or 'غير متوفرة'}
وقت الحدث: {item.incident_time or 'غير متوفر'}
التوصية: {item.recommendation or 'لا توجد'}
            """
            messagebox.showinfo("تفاصيل الخبر", details)
    
    def _edit_news(self, index):
        """Edit existing news item."""
        item = self.news_manager.get_item(index)
        if item:
            dialog = EditNewsDialog(self, item, lambda updated: self._on_news_updated(index, updated))
            self.wait_window(dialog)
    
    def _on_news_updated(self, index, updated_item):
        """Handle updated news item."""
        self.news_manager.items[index] = updated_item
        self.news_manager._save()
        self._load_news()
        messagebox.showinfo("نجاح", "تم تحديث الخبر بنجاح!")
    
    def _delete_news(self, index):
        """Delete a news item."""
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الخبر؟"):
            self.news_manager.remove_item(index)
            self._load_news()
            messagebox.showinfo("نجاح", "تم حذف الخبر بنجاح!")
    
    def _generate_report(self):
        """Generate Word report with selected items."""
        selected_items = self.news_manager.get_selected_items()
        
        if not selected_items:
            messagebox.showwarning("تحذير", "لم يتم تحديد أي أخبار للتقرير!\n\nيرجى تحديد الأخبار باستخدام خانات الاختيار.")
            return
        
        try:
            exporter = DocExporter()
            output_path = exporter.generate(selected_items)
            
            messagebox.showinfo(
                "نجاح", 
                f"✅ تم توليد التقرير بنجاح!\n\n"
                f"عدد الأخبار المضمنة: {len(selected_items)}\n"
                f"مسار الملف: {output_path}"
            )
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء توليد التقرير:\n{str(e)}")


class EditNewsDialog(ctk.CTkToplevel):
    """Dialog for editing existing news items."""
    
    def __init__(self, parent, item, on_save_callback):
        super().__init__(parent)
        self.parent = parent
        self.item = item
        self.on_save = on_save_callback
        
        self.title("✏️ تعديل الخبر")
        self.geometry("750x950")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        
        self.image_path = item.image_path
        self.image_preview = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create edit dialog widgets."""
        main_scroll = ctk.CTkScrollableFrame(self, label_text=fix_arabic_text("تعديل معلومات الخبر"))
        main_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Source
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            field_frame, 
            text="📰 المصدر *", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        ).pack(anchor="e", pady=(0, 5))
        
        self.source_var = tk.StringVar(value=self.item.source)
        ctk.CTkEntry(
            field_frame, 
            textvariable=self.source_var, 
            width=650, 
            font=ctk.CTkFont(size=13)
        ).pack(fill="x", anchor="e")
        
        # Category
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            field_frame, 
            text="📋 التصنيف", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        ).pack(anchor="e", pady=(0, 5))
        
        self.category_var = tk.StringVar(value=self.item.category)
        categories = ["عام", "سياسة", "اقتصاد", "رياضة", "تكنولوجيا", "صحة", "تعليم", "ثقافة", "منوعات", "حوادث", "طقس"]
        ctk.CTkComboBox(
            field_frame,
            values=categories,
            variable=self.category_var,
            width=650,
            font=ctk.CTkFont(size=13)
        ).pack(fill="x", anchor="e")
        
        # Title
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            field_frame, 
            text="🏷️ العنوان *", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        ).pack(anchor="e", pady=(0, 5))
        
        self.title_var = tk.StringVar(value=self.item.title)
        ctk.CTkEntry(
            field_frame, 
            textvariable=self.title_var, 
            width=650, 
            font=ctk.CTkFont(size=13)
        ).pack(fill="x", anchor="e")
        
        # Content
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            field_frame, 
            text="📝 المحتوى *", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        ).pack(anchor="e", pady=(0, 5))
        
        self.content_text = ctk.CTkTextbox(
            field_frame, 
            height=200, 
            width=650, 
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.content_text.pack(fill="x", anchor="e")
        self.content_text.insert("1.0", self.item.content)
        
        # Image section
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            field_frame, 
            text="📷 الصورة", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        ).pack(anchor="e", pady=(0, 5))
        
        img_container = ctk.CTkFrame(field_frame)
        img_container.pack(fill="x", anchor="e")
        
        btn_frame = ctk.CTkFrame(img_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            btn_frame, 
            text="📁 تغيير الصورة", 
            command=self._select_image,
            font=ctk.CTkFont(size=13),
            width=150,
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"]
        ).pack(side="right", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame, 
            text="🗑️ إزالة", 
            command=self._remove_image,
            font=ctk.CTkFont(size=13),
            width=100,
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"]
        ).pack(side="right")
        
        self.image_info_label = ctk.CTkLabel(
            img_container, 
            text=os.path.basename(self.item.image_path) if self.item.image_path else "لم يتم اختيار صورة",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        self.image_info_label.pack(anchor="e", pady=(0, 10))
        
        self.preview_frame = ctk.CTkFrame(img_container, fg_color=COLORS["bg_card"])
        self.preview_frame.pack(fill="x", pady=(0, 10))
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="معاينة الصورة",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.preview_label.pack(pady=20)
        
        if self.item.image_path and os.path.exists(self.item.image_path):
            try:
                img = Image.open(self.item.image_path)
                img.thumbnail((400, 250), Image.Resampling.LANCZOS)
                self.image_preview = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=img.size
                )
                self.preview_label.configure(image=self.image_preview, text="")
            except Exception:
                pass
        
        # Coordinates
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            field_frame, 
            text="📍 الإحداثيات", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        ).pack(anchor="e", pady=(0, 5))
        
        self.coords_var = tk.StringVar(value=self.item.coordinates or "")
        ctk.CTkEntry(
            field_frame, 
            textvariable=self.coords_var, 
            width=650, 
            font=ctk.CTkFont(size=13)
        ).pack(fill="x", anchor="e")
        
        # Incident Time
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            field_frame, 
            text="⏰ وقت الحدث", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        ).pack(anchor="e", pady=(0, 5))
        
        self.time_var = tk.StringVar(value=self.item.incident_time or "")
        ctk.CTkEntry(
            field_frame, 
            textvariable=self.time_var, 
            width=650, 
            font=ctk.CTkFont(size=13)
        ).pack(fill="x", anchor="e")
        
        # Recommendation
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            field_frame, 
            text="💡 التوصية", 
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        ).pack(anchor="e", pady=(0, 5))
        
        self.rec_text = ctk.CTkTextbox(
            field_frame, 
            height=120, 
            width=650, 
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.rec_text.pack(fill="x", anchor="e")
        if self.item.recommendation:
            self.rec_text.insert("1.0", self.item.recommendation)
        
        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            button_frame, 
            text="✅ حفظ التعديلات", 
            command=self._save,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            width=200,
            height=50
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame, 
            text="❌ إلغاء", 
            command=self.destroy,
            font=ctk.CTkFont(size=15),
            fg_color="#757575",
            hover_color="#616161",
            width=150,
            height=50
        ).pack(side="left")
    
    def _select_image(self):
        """Select new image."""
        file_path = filedialog.askopenfilename(
            title="اختر صورة",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.image_path = file_path
            filename = os.path.basename(file_path)
            self.image_info_label.configure(
                text=f"📄 {filename}",
                text_color=COLORS["success"]
            )
            
            try:
                img = Image.open(file_path)
                img.thumbnail((400, 250), Image.Resampling.LANCZOS)
                self.image_preview = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=img.size
                )
                self.preview_label.configure(image=self.image_preview, text="")
            except Exception as e:
                self.preview_label.configure(text=f"⚠️ خطأ: {str(e)}")
    
    def _remove_image(self):
        """Remove image."""
        self.image_path = None
        self.image_preview = None
        self.image_info_label.configure(
            text="لم يتم اختيار صورة",
            text_color=COLORS["text_secondary"]
        )
        self.preview_label.configure(image=None, text="معاينة الصورة")
    
    def _save(self):
        """Validate and save changes."""
        source = self.source_var.get().strip()
        title = self.title_var.get().strip()
        content = self.content_text.get("1.0", "end").strip()
        
        if not source:
            messagebox.showerror("خطأ", "يرجى إدخال المصدر", parent=self)
            return
        
        if not title:
            messagebox.showerror("خطأ", "يرجى إدخال العنوان", parent=self)
            return
        
        if not content:
            messagebox.showerror("خطأ", "يرجى إدخال المحتوى", parent=self)
            return
        
        updated_item = NewsItem(
            id=self.item.id,
            source=source,
            title=title,
            content=content,
            category=self.category_var.get().strip() or "عام",
            image_path=self.image_path,
            coordinates=self.coords_var.get().strip(),
            incident_time=self.time_var.get().strip(),
            recommendation=self.rec_text.get("1.0", "end").strip(),
            created_at=self.item.created_at,
            selected_for_report=self.item.selected_for_report
        )
        
        self.on_save(updated_item)
        self.destroy()


if __name__ == "__main__":
    app = ModernNewsApp()
    app.mainloop()
