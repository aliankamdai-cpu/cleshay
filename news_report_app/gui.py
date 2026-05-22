"""Main GUI application for news report generation."""

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
from PIL import Image, ImageTk

from models import NewsItem
from doc_generator import DocExporter


# Set appearance mode and default color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class NewsManager:
    """Manages the collection of news items."""
    
    def __init__(self):
        self.items: List[NewsItem] = []
        self.sources: List[str] = []  # Track unique sources
        self.data_file = Path(__file__).parent / "output" / "news_data.json"
        self._load()
    
    def _load(self):
        """Load news items from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
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
    
    def __len__(self) -> int:
        return len(self.items)


class NewsDialog(ctk.CTkToplevel):
    """Modal dialog for adding/editing news items with enhanced UI."""
    
    def __init__(self, parent, on_save_callback, sources: List[str] = None):
        super().__init__(parent)
        self.parent = parent
        self.on_save = on_save_callback
        self.available_sources = sources or []
        
        self.title("✨ إضافة خبر جديد")
        self.geometry("700x900")
        self.resizable(True, True)
        self.minsize(600, 800)
        self.transient(parent)
        self.grab_set()
        
        self.image_path: Optional[str] = None
        self.image_preview = None
        self.preview_label = None
        
        self._create_widgets()
        self._center_window()
    
    def _center_window(self):
        """Center the dialog on parent window."""
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (700 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (900 // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create all dialog widgets with modern styling."""
        # Main scrollable frame
        main_scroll = ctk.CTkScrollableFrame(self, label_text="معلومات الخبر")
        main_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header section
        header_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="📝 إضافة خبر جديد",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#4CAF50"
        )
        title_label.pack(side="right")
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="يرجى ملء المعلومات أدناه",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack(side="right", padx=(0, 10), pady=(5, 0))
        
        # Required fields note
        note_frame = ctk.CTkFrame(main_scroll, fg_color="#FF980020")
        note_frame.pack(fill="x", pady=(0, 20))
        note_label = ctk.CTkLabel(
            note_frame,
            text="⚠️ الحقول المميزة بـ (*) مطلوبة",
            font=ctk.CTkFont(size=11),
            text_color="#FF9800"
        )
        note_label.pack(pady=8)
        
        # Source - with dropdown
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        source_label = ctk.CTkLabel(
            field_frame, 
            text="📰 المصدر *", 
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="e"
        )
        source_label.pack(anchor="e", pady=(0, 5))
        
        self.source_var = tk.StringVar()
        self.source_combo = ctk.CTkComboBox(
            field_frame, 
            values=self.available_sources + ["--- مصدر جديد ---"],
            variable=self.source_var,
            width=600,
            font=ctk.CTkFont(size=12),
            dropdown_font=ctk.CTkFont(size=12),
            state="readonly"
        )
        self.source_combo.pack(fill="x", anchor="e")
        self.source_combo.set("")
        self.source_combo.bind("<<ComboboxSelected>>", self._on_source_selected)
        
        # Category/Classification
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        category_label = ctk.CTkLabel(
            field_frame, 
            text="📋 تصنيف الخبر", 
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="e"
        )
        category_label.pack(anchor="e", pady=(0, 5))
        
        self.category_var = tk.StringVar()
        categories = ["عام", "سياسة", "اقتصاد", "رياضة", "تكنولوجيا", "صحة", "تعليم", "ثقافة", "منوعات", "حوادث", "طقس"]
        self.category_combo = ctk.CTkComboBox(
            field_frame, 
            values=categories,
            variable=self.category_var,
            width=600,
            font=ctk.CTkFont(size=12),
            dropdown_font=ctk.CTkFont(size=12),
            state="readonly"
        )
        self.category_combo.pack(fill="x", anchor="e")
        self.category_combo.set("")
        
        # Title
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ctk.CTkLabel(
            field_frame, 
            text="🏷️ العنوان/رأس الخبر *", 
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="e"
        )
        title_label.pack(anchor="e", pady=(0, 5))
        
        self.title_var = tk.StringVar()
        self.title_entry = ctk.CTkEntry(
            field_frame, 
            textvariable=self.title_var, 
            width=600, 
            font=ctk.CTkFont(size=12),
            placeholder_text="أدخل عنوان الخبر هنا..."
        )
        self.title_entry.pack(fill="x", anchor="e")
        
        # Content
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        content_label = ctk.CTkLabel(
            field_frame, 
            text="📝 المحتوى/نص الخبر *", 
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="e"
        )
        content_label.pack(anchor="e", pady=(0, 5))
        
        self.content_text = ctk.CTkTextbox(
            field_frame, 
            height=180, 
            width=600, 
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        self.content_text.pack(fill="x", anchor="e")
        self.content_text.bind("<Control-v>", self._on_paste)
        self.content_text.bind("<Control-V>", self._on_paste)
        
        # Image section with preview
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        image_label = ctk.CTkLabel(
            field_frame, 
            text="📷 الصورة المرفقة", 
            font=ctk.CTkFont(size=13, weight="bold"),
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
            font=ctk.CTkFont(size=12),
            width=150,
            fg_color="#2196F3",
            hover_color="#1976D2"
        ).pack(side="right", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame, 
            text="🗑️ إزالة", 
            command=self._remove_image,
            font=ctk.CTkFont(size=12),
            width=100,
            fg_color="#F44336",
            hover_color="#D32F2F"
        ).pack(side="right")
        
        self.image_info_label = ctk.CTkLabel(
            img_container, 
            text="لم يتم اختيار صورة", 
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="e"
        )
        self.image_info_label.pack(anchor="e", pady=(0, 10))
        
        # Image preview
        self.preview_frame = ctk.CTkFrame(img_container, fg_color="#2a2a2a")
        self.preview_frame.pack(fill="x", pady=(0, 10))
        
        self.preview_label = ctk.CTkLabel(
            self.preview_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.preview_label.pack(pady=20)
        
        # Coordinates
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        coords_label = ctk.CTkLabel(
            field_frame, 
            text="📍 الإحداثيات/الموقع", 
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="e"
        )
        coords_label.pack(anchor="e", pady=(0, 5))
        
        self.coords_var = tk.StringVar()
        self.coords_entry = ctk.CTkEntry(
            field_frame, 
            textvariable=self.coords_var, 
            width=600, 
            font=ctk.CTkFont(size=12),
            placeholder_text="مثال: 24.7136° N, 46.6753° E"
        )
        self.coords_entry.pack(fill="x", anchor="e")
        
        # Incident Time
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        time_label = ctk.CTkLabel(
            field_frame, 
            text="⏰ وقت الحدث", 
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="e"
        )
        time_label.pack(anchor="e", pady=(0, 5))
        
        self.time_var = tk.StringVar()
        self.time_entry = ctk.CTkEntry(
            field_frame, 
            textvariable=self.time_var, 
            width=600, 
            font=ctk.CTkFont(size=12),
            placeholder_text="مثال: 2024-01-15 14:30"
        )
        self.time_entry.pack(fill="x", anchor="e")
        
        # Recommendation
        field_frame = ctk.CTkFrame(main_scroll, fg_color="transparent")
        field_frame.pack(fill="x", pady=(0, 15))
        
        rec_label = ctk.CTkLabel(
            field_frame, 
            text="💡 توصية أو ملاحظة إضافية", 
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="e"
        )
        rec_label.pack(anchor="e", pady=(0, 5))
        
        self.rec_text = ctk.CTkTextbox(
            field_frame, 
            height=100, 
            width=600, 
            font=ctk.CTkFont(size=12),
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
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#4CAF50",
            hover_color="#45A049",
            width=200,
            height=45
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame, 
            text="❌ إلغاء", 
            command=self.destroy,
            font=ctk.CTkFont(size=14),
            fg_color="#757575",
            hover_color="#616161",
            width=150,
            height=45
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
            filesize = os.path.getsize(file_path) / 1024  # KB
            
            self.image_info_label.configure(
                text=f"📄 {filename} ({filesize:.1f} KB)",
                text_color="#4CAF50"
            )
            
            # Create preview
            try:
                img = Image.open(file_path)
                img.thumbnail((300, 200), Image.Resampling.LANCZOS)
                self.image_preview = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(img.width, img.height)
                )
                self.preview_label.configure(image=self.image_preview, text="")
                self.preview_frame.configure(height=img.height + 40)
            except Exception as e:
                print(f"Error loading image preview: {e}")
                self.preview_label.configure(text="⚠️ تعذر عرض المعاينة")
    
    def _remove_image(self):
        """Remove selected image."""
        self.image_path = None
        self.image_preview = None
        self.image_info_label.configure(
            text="لم يتم اختيار صورة",
            text_color="gray"
        )
        self.preview_label.configure(image=None, text="")
        self.preview_frame.configure(height=60)
    
    def _on_paste(self, event=None):
        """Handle Ctrl+V paste by inserting clipboard text at the cursor position."""
        try:
            import pyperclip
            text = pyperclip.paste()
            widget = event.widget
            widget.insert("insert", text)
            return "break"
        except Exception as e:
            print(f"Paste error: {e}")
            return "break"

    def _save(self):
        """Validate and save the news item."""
        source = self.source_var.get().strip()
        title = self.title_var.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()
        
        errors = []
        if not source:
            errors.append("المصدر")
        if not title:
            errors.append("العنوان")
        if not content:
            errors.append("المحتوى")
        
        if errors:
            error_msg = "يرجى ملء الحقول المطلوبة:\n" + "\n".join([f"• {field}" for field in errors])
            messagebox.showerror("⚠️ حقول ناقصة", error_msg, parent=self)
            return
        
        item = NewsItem(
            source=source,
            title=title,
            content=content,
            category=self.category_var.get().strip(),
            image_path=self.image_path,
            coordinates=self.coords_var.get().strip() or None,
            incident_time=self.time_var.get().strip() or None,
            recommendation=self.rec_text.get("1.0", "end-1c").strip() or None,
        )
        
        self.on_save(item)
        self.destroy()


class NewsReportApp(ctk.CTk):
    """Main application window with modern design."""
    
    def __init__(self):
        super().__init__()
        
        self.title("✨ نظام إدارة التقارير الإخبارية")
        self.geometry("1100x750")
        self.minsize(900, 600)
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.manager = NewsManager()
        
        self._create_widgets()
        self._refresh_list()
    
    def _create_widgets(self):
        """Create the main application widgets with modern styling."""
        # Header section
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📰 نظام إدارة التقارير الإخبارية",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#4CAF50"
        )
        title_label.pack(side="right")
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="إدارة وتوليد التقارير الإخبارية بسهولة",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.pack(side="right", padx=(0, 15), pady=(8, 0))
        
        # Stats frame
        stats_frame = ctk.CTkFrame(header_frame, fg_color="#2a2a2a")
        stats_frame.pack(side="left", padx=(0, 10))
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text=f"📊 عدد الأخبار: {len(self.manager.items)}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2196F3"
        )
        self.stats_label.pack(pady=10, padx=20)
        
        # Top toolbar with better styling
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkButton(
            toolbar, 
            text="➕ إضافة خبر جديد", 
            command=self._add_news,
            fg_color="#4CAF50",
            hover_color="#45A049",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=180,
            height=40,
            corner_radius=8
        ).pack(side="right", padx=(0, 10))
        
        ctk.CTkButton(
            toolbar, 
            text="🗑️ حذف المحدد", 
            command=self._delete_selected,
            fg_color="#F44336",
            hover_color="#D32F2F",
            font=ctk.CTkFont(size=13),
            width=140,
            height=40,
            corner_radius=8
        ).pack(side="right", padx=(0, 10))
        
        ctk.CTkButton(
            toolbar, 
            text="🗑️ حذف الكل", 
            command=self._clear_all,
            fg_color="#FF9800",
            hover_color="#F57C00",
            font=ctk.CTkFont(size=13),
            width=120,
            height=40,
            corner_radius=8
        ).pack(side="right", padx=(0, 10))
        
        ctk.CTkButton(
            toolbar, 
            text="📄 توليد التقرير Word", 
            command=self._generate_report,
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=200,
            height=40,
            corner_radius=8
        ).pack(side="left", padx=(0, 10))
        
        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            search_frame,
            text="🔍 بحث:",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(side="right", padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self._filter_list())
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=300,
            font=ctk.CTkFont(size=12),
            placeholder_text="ابحث بالعنوان أو المصدر..."
        )
        self.search_entry.pack(side="right", fill="x", expand=True)
        
        # News list with better styling
        list_container = ctk.CTkFrame(self)
        list_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Treeview styling
        self.style.configure("Treeview",
                            background="#2a2a2a",
                            foreground="white",
                            fieldbackground="#2a2a2a",
                            font=ctk.CTkFont(size=11),
                            rowheight=35)
        self.style.map("Treeview",
                      background=[('selected', '#2196F3')],
                      foreground=[('selected', 'white')])
        self.style.configure("Treeview.Heading",
                            background="#1e1e1e",
                            foreground="#4CAF50",
                            font=ctk.CTkFont(size=12, weight="bold"))
        self.style.map("Treeview.Heading",
                      background=[('active', '#333333')])
        
        columns = ("#", "✓", "المصدر", "العنوان", "التصنيف", "المرفقات")
        self.tree = ttk.Treeview(list_container, columns=columns, show="headings", height=20)
        
        self.tree.heading("#", text="#")
        self.tree.heading("✓", text="تحديد")
        self.tree.heading("المصدر", text="المصدر")
        self.tree.heading("العنوان", text="العنوان")
        self.tree.heading("التصنيف", text="التصنيف")
        self.tree.heading("المرفقات", text="المرفقات")
        
        self.tree.column("#", width=40, anchor="center")
        self.tree.column("✓", width=60, anchor="center")
        self.tree.column("المصدر", width=150, anchor="center")
        self.tree.column("العنوان", width=400, anchor="w")
        self.tree.column("التصنيف", width=100, anchor="center")
        self.tree.column("المرفقات", width=120, anchor="center")
        
        # Custom scrollbar
        scrollbar = ctk.CTkScrollbar(list_container, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", padx=(5, 0))
        
        # Store checkbox widgets
        self.checkboxes = {}
        
        # Bind click on checkbox column to toggle
        self.tree.bind("<Button-1>", self._on_checkbox_click)
        
        # Footer
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        info_label = ctk.CTkLabel(
            footer_frame,
            text="💡 تلميح: انقر على مربع التحديد ✓ لاختيار الأخبار للتقرير",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        info_label.pack(side="right")
        
        # Bind double-click to toggle selection and right-click for context menu
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        # Create context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="✓ تحديد/إلغاء التحديد", command=self._toggle_selected)
        self.context_menu.add_command(label="✓ تحديد الكل", command=self._select_all)
        self.context_menu.add_command(label="✗ إلغاء تحديد الكل", command=self._deselect_all)
    
    def _on_checkbox_click(self, event):
        """Handle click on checkbox column to toggle selection."""
        column = self.tree.identify_column(event.x)
        
        # Check if click is in the checkbox column (column #2 which is index 1)
        if column == "#2":  # Checkbox column
            item = self.tree.identify_row(event.y)
            if item:
                # Get the news item from our checkboxes dict
                news_item = self.checkboxes.get(item)
                if news_item:
                    # Toggle selection
                    current_selection = getattr(news_item, 'selected_for_report', True)
                    news_item.selected_for_report = not current_selection
                    self._refresh_list()
    
    def _on_tree_double_click(self, event=None):
        """Handle double-click on tree item to toggle selection."""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            index = int(item["values"][0]) - 1
            news_item = self.manager.get_item(index)
            if news_item:
                # Toggle selection
                current_selection = getattr(news_item, 'selected_for_report', True)
                news_item.selected_for_report = not current_selection
                self._refresh_list()
    
    def _show_context_menu(self, event):
        """Show context menu for selection options."""
        self.context_menu.tk_popup(event.x_root, event.y_root)
    
    def _toggle_selected(self):
        """Toggle selection status of the currently selected item."""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            index = int(item["values"][0]) - 1
            news_item = self.manager.get_item(index)
            if news_item:
                current_selection = getattr(news_item, 'selected_for_report', True)
                news_item.selected_for_report = not current_selection
                self._refresh_list()
    
    def _select_all(self):
        """Select all items for report."""
        for news_item in self.manager.items:
            news_item.selected_for_report = True
        self._refresh_list()
    
    def _deselect_all(self):
        """Deselect all items for report."""
        for news_item in self.manager.items:
            news_item.selected_for_report = False
        self._refresh_list()
    
    def _filter_list(self):
        """Filter the news list based on search query."""
        query = self.search_var.get().strip().lower()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clear checkboxes dict
        self.checkboxes.clear()
        
        for i, news_item in enumerate(self.manager.items, 1):
            if not query or \
               query in news_item.title.lower() or \
               query in news_item.source.lower() or \
               (news_item.content and query in news_item.content.lower()) or \
               (news_item.category and query in news_item.category.lower()):
                # Check if item is selected for report (default: all selected)
                checkmark = "✓" if getattr(news_item, 'selected_for_report', True) else ""
                item_id = self.tree.insert("", "end", values=(
                    i,
                    checkmark,
                    news_item.source,
                    news_item.title,
                    news_item.category or "",
                    news_item.get_attachments_summary()
                ))
                # Store reference to this item's selection state
                self.checkboxes[item_id] = news_item
    
    def _update_stats(self):
        """Update the statistics display."""
        self.stats_label.configure(text=f"📊 عدد الأخبار: {len(self.manager.items)}")
    
    def _refresh_list(self):
        """Refresh the news list display."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clear checkboxes dict
        self.checkboxes.clear()
        
        for i, news_item in enumerate(self.manager.items, 1):
            # Check if item is selected for report (default: all selected)
            checkmark = "✓" if getattr(news_item, 'selected_for_report', True) else ""
            item_id = self.tree.insert("", "end", values=(
                i,
                checkmark,
                news_item.source,
                news_item.title,
                news_item.category or "",
                news_item.get_attachments_summary()
            ))
            # Store reference to this item's selection state
            self.checkboxes[item_id] = news_item
        
        self._update_stats()
        self._filter_list()  # Apply current filter
    
    def _add_news(self):
        """Open the add news dialog."""
        dialog = NewsDialog(
            self,
            on_save_callback=self._on_news_saved,
            sources=self.manager.sources
        )
        self.wait_window(dialog)
    
    def _on_news_saved(self, item: NewsItem):
        """Callback when a news item is saved from the dialog."""
        self.manager.add_item(item)
        self._refresh_list()
    
    def _delete_selected(self):
        """Delete the selected news item."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("⚠️ تحذير", "يرجى تحديد خبر للحذف")
            return
        
        item = self.tree.item(selected[0])
        index = int(item["values"][0]) - 1
        
        if messagebox.askyesno("✅ تأكيد", "هل أنت متأكد من حذف هذا الخبر؟"):
            self.manager.remove_item(index)
            self._refresh_list()
    
    def _clear_all(self):
        """Clear all news items."""
        if not self.manager.items:
            messagebox.showinfo("ℹ️ معلومات", "لا توجد أخبار للحذف")
            return
        
        if messagebox.askyesno("✅ تأكيد", "هل أنت متأكد من حذف جميع الأخبار؟"):
            self.manager.clear()
            self._refresh_list()
    
    def _generate_report(self):
        """Generate the Word document report with selected items only."""
        # Filter to get only selected items
        selected_items = [item for item in self.manager.items if getattr(item, 'selected_for_report', True)]
        
        if not selected_items:
            messagebox.showwarning("⚠️ تحذير", "لا توجد أخبار محددة لتوليد التقرير.\n\nيرجى تحديد خبر واحد على الأقل بالنقر المزدوج عليه أو استخدام قائمة الخيارات.")
            return
        
        try:
            exporter = DocExporter()
            filepath = exporter.generate(selected_items)
            messagebox.showinfo("نجح", f"تم توليد التقرير بنجاح ({len(selected_items)} خبر):\n{filepath}")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء توليد التقرير:\n{str(e)}")


if __name__ == "__main__":
    app = NewsReportApp()
    app.mainloop()
