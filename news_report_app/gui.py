"""Main GUI application for news report generation."""

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional
from pathlib import Path

import customtkinter as ctk

from models import NewsItem
from doc_generator import DocExporter


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
                            image_path=item_data.get('image_path'),
                            coordinates=item_data.get('coordinates'),
                            incident_time=item_data.get('incident_time'),
                            recommendation=item_data.get('recommendation'),
                            created_at=__import__('datetime').datetime.fromisoformat(item_data.get('created_at', __import__('datetime').datetime.now().isoformat()))
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
                    'image_path': item.image_path,
                    'coordinates': item.coordinates,
                    'incident_time': item.incident_time,
                    'recommendation': item.recommendation,
                    'created_at': item.created_at.isoformat()
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
    """Modal dialog for adding/editing news items."""
    
    def __init__(self, parent, on_save_callback, sources: List[str] = None):
        super().__init__(parent)
        self.parent = parent
        self.on_save = on_save_callback
        self.available_sources = sources or []
        
        self.title("إضافة خبر جديد")
        self.geometry("600x850")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.image_path: Optional[str] = None
        
        self._create_widgets()
        self._center_window()
    
    def _center_window(self):
        """Center the dialog on parent window."""
        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (600 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (850 // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create all dialog widgets."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Source - with dropdown
        ctk.CTkLabel(main_frame, text="📰 المصدر (مطلوب)", font=("Arial", 12)).pack(anchor="e", pady=(10, 0))
        self.source_var = tk.StringVar()
        self.source_combo = ctk.CTkComboBox(
            main_frame, 
            values=self.available_sources,
            variable=self.source_var,
            width=500,
            font=("Arial", 12)
        )
        self.source_combo.pack(fill="x", pady=(0, 10))
        self.source_combo.set("")  # Allow empty for new source
        
        # Title
        ctk.CTkLabel(main_frame, text="🏷️ العنوان/رأس الخبر (مطلوب)", font=("Arial", 12)).pack(anchor="e", pady=(10, 0))
        self.title_var = tk.StringVar()
        self.title_entry = ctk.CTkEntry(main_frame, textvariable=self.title_var, width=500, font=("Arial", 12))
        self.title_entry.pack(fill="x", pady=(0, 10))
        
        # Content
        ctk.CTkLabel(main_frame, text="📝 المحتوى/نص الخبر (مطلوب)", font=("Arial", 12)).pack(anchor="e", pady=(10, 0))
        self.content_text = ctk.CTkTextbox(main_frame, height=150, width=500, font=("Arial", 12))
        self.content_text.pack(fill="x", pady=(0, 10))
        # --- FIX: Enable paste (Ctrl+V) in the content textbox ---
        self.content_text.bind("<Control-v>", self._on_paste)
        self.content_text.bind("<Control-V>", self._on_paste)
        
        # Image
        ctk.CTkLabel(main_frame, text="📷 صورة (اختياري)", font=("Arial", 12)).pack(anchor="e", pady=(10, 0))
        img_frame = ctk.CTkFrame(main_frame)
        img_frame.pack(fill="x", pady=(0, 10))
        self.image_label = ctk.CTkLabel(img_frame, text="لم يتم اختيار صورة", font=("Arial", 12))
        self.image_label.pack(side="right", padx=(0, 10))
        ctk.CTkButton(img_frame, text="اختر صورة", command=self._select_image, font=("Arial", 12)).pack(side="right")
        
        # Coordinates
        ctk.CTkLabel(main_frame, text="📍 إحداثيات/موقع (اختياري)", font=("Arial", 12)).pack(anchor="e", pady=(10, 0))
        self.coords_var = tk.StringVar()
        self.coords_entry = ctk.CTkEntry(main_frame, textvariable=self.coords_var, width=500, font=("Arial", 12))
        self.coords_entry.pack(fill="x", pady=(0, 10))
        
        # Incident Time
        ctk.CTkLabel(main_frame, text="⏰ وقت الحدث (اختياري)", font=("Arial", 12)).pack(anchor="e", pady=(10, 0))
        self.time_var = tk.StringVar()
        self.time_entry = ctk.CTkEntry(main_frame, textvariable=self.time_var, width=500, font=("Arial", 12))
        self.time_entry.pack(fill="x", pady=(0, 10))
        
        # Recommendation
        ctk.CTkLabel(main_frame, text="💡 توصية أو ملاحظة إضافية (اختياري)", font=("Arial", 12)).pack(anchor="e", pady=(10, 0))
        self.rec_text = ctk.CTkTextbox(main_frame, height=80, width=500, font=("Arial", 12))
        self.rec_text.pack(fill="x", pady=(0, 10))
        # --- FIX: Enable paste (Ctrl+V) in the recommendation textbox ---
        self.rec_text.bind("<Control-v>", self._on_paste)
        self.rec_text.bind("<Control-V>", self._on_paste)
        
        # Save button
        ctk.CTkButton(main_frame, text="✅ حفظ الخبر", command=self._save,
                     fg_color="#2E8B57", hover_color="#3CB371", font=("Arial", 12)).pack(pady=20)
    
    def _select_image(self):
        """Open file dialog to select an image."""
        file_path = filedialog.askopenfilename(
            title="اختر صورة",
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            self.image_path = file_path
            filename = os.path.basename(file_path)
            self.image_label.configure(text=filename)
    
    def _on_paste(self, event=None):
        """Handle Ctrl+V paste by inserting clipboard text at the cursor position."""
        try:
            text = self.clipboard_get()
            widget = event.widget if event else self.focus_get()
            if widget:
                # Insert text at the current cursor position
                if widget.index("insert") != "1.0":
                    pass  # use default insert position
                widget.insert("insert", text)
            return "break"  # Prevent default handling
        except Exception:
            return "break"

    def _save(self):
        """Validate and save the news item."""
        source = self.source_var.get().strip()
        title = self.title_var.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()
        
        if not source or not title or not content:
            messagebox.showerror("خطأ", "يرجى ملء الحقول المطلوبة: المصدر، العنوان، والمحتوى", parent=self)
            return
        
        item = NewsItem(
            source=source,
            title=title,
            content=content,
            image_path=self.image_path,
            coordinates=self.coords_var.get().strip() or None,
            incident_time=self.time_var.get().strip() or None,
            recommendation=self.rec_text.get("1.0", "end-1c").strip() or None,
        )
        
        self.on_save(item)
        self.destroy()


class NewsReportApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.title("تقرير الأخبار")
        self.geometry("900x700")
        
        self.manager = NewsManager()
        
        self._create_widgets()
        self._refresh_list()
    
    def _create_widgets(self):
        """Create the main application widgets."""
        # Top toolbar
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            toolbar, text="➕ إضافة خبر", command=self._add_news,
            fg_color="#2E8B57", hover_color="#3CB371", font=("Arial", 12)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            toolbar, text="🗑️ حذف المحدد", command=self._delete_selected,
            fg_color="#DC143C", hover_color="#FF4500", font=("Arial", 12)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            toolbar, text="🗑️ حذف الكل", command=self._clear_all,
            fg_color="#8B0000", hover_color="#B22222", font=("Arial", 12)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            toolbar, text="📄 توليد التقرير", command=self._generate_report,
            fg_color="#1E90FF", hover_color="#4169E1", font=("Arial", 12)
        ).pack(side="right", padx=5)
        
        # News list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        columns = ("#", "المصدر", "العنوان", "المرفقات")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        self.tree.heading("#", text="#")
        self.tree.heading("المصدر", text="المصدر")
        self.tree.heading("العنوان", text="العنوان")
        self.tree.heading("المرفقات", text="المرفقات")
        
        self.tree.column("#", width=40, anchor="center")
        self.tree.column("المصدر", width=150, anchor="center")
        self.tree.column("العنوان", width=400, anchor="w")
        self.tree.column("المرفقات", width=120, anchor="center")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def _refresh_list(self):
        """Refresh the news list display."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, news_item in enumerate(self.manager.items, 1):
            self.tree.insert("", "end", values=(
                i,
                news_item.source,
                news_item.title,
                news_item.get_attachments_summary()
            ))
    
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
            messagebox.showwarning("تحذير", "يرجى تحديد خبر للحذف")
            return
        
        item = self.tree.item(selected[0])
        index = int(item["values"][0]) - 1
        
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا الخبر؟"):
            self.manager.remove_item(index)
            self._refresh_list()
    
    def _clear_all(self):
        """Clear all news items."""
        if not self.manager.items:
            messagebox.showinfo("معلومات", "لا توجد أخبار للحذف")
            return
        
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف جميع الأخبار؟"):
            self.manager.clear()
            self._refresh_list()
    
    def _generate_report(self):
        """Generate the Word document report."""
        if not self.manager.items:
            messagebox.showwarning("تحذير", "لا توجد أخبار لتوليد التقرير")
            return
        
        try:
            exporter = DocExporter()
            filepath = exporter.generate(self.manager.items)
            messagebox.showinfo("نجح", f"تم توليد التقرير بنجاح:\n{filepath}")
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء توليد التقرير:\n{str(e)}")


if __name__ == "__main__":
    app = NewsReportApp()
    app.mainloop()
