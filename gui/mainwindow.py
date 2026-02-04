import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QFrame, QProgressBar, QMessageBox,
                             QComboBox, QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl, QBuffer
from PyQt6.QtGui import QPixmap, QImage, QIcon, QDragEnterEvent, QDropEvent, QAction
from PIL import Image, ImageQt
import time

# Import core logic
from core.remover import remove_background

class Worker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, image, model_name, alpha_matting, post_process):
        super().__init__()
        self.image = image
        self.model_name = model_name
        self.alpha_matting = alpha_matting
        self.post_process = post_process

    def run(self):
        try:
            # Pass all parameters to the removal function
            result = remove_background(
                self.image, 
                model_name=self.model_name, 
                alpha_matting=self.alpha_matting,
                post_process=self.post_process
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class ImageDropLabel(QLabel):
    fileDropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("\n\n\nDrag & Drop Image Here\nor Click to Browse\n\n\n")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #5c5c5c;
                border-radius: 10px;
                color: #aaaaaa;
                font-size: 16px;
                background-color: #2b2b2b;
            }
            QLabel:hover {
                border: 2px dashed #3498db;
                background-color: #323232;
                color: #ffffff;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.fileDropped.emit(files[0])

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Trigger file dialog from parent
            self.window().open_file_dialog()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Background Remover - By Faseeh Ansari")
        self.setGeometry(100, 100, 1000, 700)
        self.setAcceptDrops(True) # Enable drops for the whole window
        
        # Initialize state
        self.original_image = None
        self.processed_image = None
        self.current_file_path = None

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header_label = QLabel("Background Remover")
        header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        # Content Area (Drop Zone or Split View)
        self.content_area = QWidget()
        self.content_layout = QHBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Initial Drop Zone
        self.drop_label = ImageDropLabel()
        self.drop_label.fileDropped.connect(self.process_image_path)
        
        # Image Projectors (Hidden initially)
        self.original_label = QLabel()
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setStyleSheet("border: 1px solid #444; background: #222; border-radius: 8px;")
        self.original_label.setMinimumSize(300, 400)
        
        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("border: 1px solid #444; background: #222; border-radius: 8px;")
        self.result_label.setMinimumSize(300, 400)

        # Add to layout
        # We start with just the drop label
        self.content_layout.addWidget(self.drop_label)
        
        main_layout.addWidget(self.content_area, stretch=1)

        # Progress Bar (Hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #333;
                height: 4px;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()

        self.btn_open = QPushButton("Open Image")
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_file_dialog)
        
        self.btn_save = QPushButton("Save Result")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setEnabled(False) 
        self.btn_save.clicked.connect(self.save_image)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #3498db; 
                color: white; 
                border: none; 
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)

        self.btn_clear = QPushButton("Reset")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.reset_ui)
        self.btn_clear.hide()

        controls_layout.addWidget(self.btn_open)
        controls_layout.addWidget(self.btn_save) # Moved save button here
        
        # Advanced Controls Group
        settings_group = QGroupBox("Advanced Settings")
        settings_group.setStyleSheet("QGroupBox { border: 1px solid #333; border-radius: 5px; margin-top: 10px; padding-top: 5px; color: #888; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(10, 15, 10, 10)
        
        # Model Selector
        self.combo_model = QComboBox()
        self.combo_model.addItem("IS-Net (General Use - Best)", "isnet-general-use")
        self.combo_model.addItem("U2-Net (Standard)", "u2net")
        self.combo_model.addItem("Human Segmentation", "u2net_human_seg")
        self.combo_model.addItem("Cloth/Product", "u2net_cloth_seg")
        self.combo_model.setStyleSheet("QComboBox { background: #333; color: white; padding: 5px; border-radius: 3px; } QComboBox::drop-down { border: none; }")
        
        # Checkboxes
        self.chk_alpha = QCheckBox("Refine Edges")
        self.chk_alpha.setChecked(True) # Default On
        self.chk_alpha.setToolTip("Enable for hair/fur details. Disable for hard objects.")
        self.chk_alpha.setStyleSheet("QCheckBox { color: #ccc; }")
        
        self.chk_post = QCheckBox("Post-Process")
        self.chk_post.setChecked(True) # Default On
        self.chk_post.setToolTip("Cleans up small floating pixels.")
        self.chk_post.setStyleSheet("QCheckBox { color: #ccc; }")

        settings_layout.addWidget(QLabel("Model:"))
        settings_layout.addWidget(self.combo_model, 1)
        settings_layout.addWidget(self.chk_alpha)
        settings_layout.addWidget(self.chk_post)
        
        settings_group.setLayout(settings_layout)
        
        # Add to main layout (Insert before controls)
        main_layout.addWidget(settings_group)
        main_layout.addLayout(controls_layout)

        controls_layout.addWidget(self.btn_clear)
        controls_layout.addStretch()

        # Watermark
        self.watermark_label = QLabel("Developed by Faseeh Ansari")
        self.watermark_label.setStyleSheet("color: #555; font-size: 20px; font-style: italic;")
        self.watermark_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.watermark_label)

        # Status Bar
        self.status_label = QLabel("Ready - Drag image or Ctrl+V to paste")
        self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        self.statusBar().addWidget(self.status_label)
        self.statusBar().setStyleSheet("background: #1e1e1e; border-top: 1px solid #333;")

        # Set App Icon
        if os.path.exists("icon.png"):
            self.setWindowIcon(QIcon("icon.png"))
            # Optional: Add logo to header if desired
            # for now, Window Icon is sufficient for professional feel

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QPushButton {
                background-color: #444; 
                color: white; 
                border: none; 
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.process_image_path(files[0])

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            if mime_data.hasImage():
                pixmap = clipboard.pixmap()
                self.process_run_from_pixmap(pixmap)
            elif mime_data.hasUrls(): # file copy
                files = [u.toLocalFile() for u in mime_data.urls()]
                if files:
                    self.process_image_path(files[0])

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if file_path:
            self.process_image_path(file_path)

    def process_run_from_pixmap(self, pixmap):
        self.current_file_path = None # From clipboard
        self.status_label.setText(f"Loading image from clipboard...")
        
        try:
            # Convert QPixmap to PIL Image
            import io
            buffer = QBuffer()
            buffer.open(QBuffer.OpenModeFlag.ReadWrite)
            pixmap.save(buffer, "PNG")
            pil_im = Image.open(io.BytesIO(buffer.data()))
            
            self.original_image = pil_im
            self.setup_split_view()
            self.display_image(self.original_image, self.original_label)
            self.start_removal_thread()
        except NameError:
             from PyQt6.QtCore import QBuffer
             # Retry logic or just import it at top. 
             # I will assume I need to add QBuffer to imports or do it here.
             buffer = QBuffer()
             buffer.open(QBuffer.OpenModeFlag.ReadWrite)
             pixmap.save(buffer, "PNG")
             pil_im = Image.open(io.BytesIO(buffer.data()))
             self.original_image = pil_im
             self.setup_split_view()
             self.display_image(self.original_image, self.original_label)
             self.start_removal_thread()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load clipboard image: {str(e)}")

    def process_image_path(self, file_path):
        self.current_file_path = file_path
        self.status_label.setText(f"Loading {os.path.basename(file_path)}...")
        
        try:
            self.original_image = Image.open(file_path)
            # Fix orientation or format if needed
            self.original_image.load() # Force load
            
            self.setup_split_view()
            self.display_image(self.original_image, self.original_label)
            self.start_removal_thread()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")

    def setup_split_view(self):
        # Remove drop label if present
        self.drop_label.setParent(None)
        
        # Add labels if not already in layout
        if self.content_layout.indexOf(self.original_label) == -1:
            self.content_layout.addWidget(self.original_label, 1)
            self.content_layout.addWidget(self.result_label, 1)
        
        self.btn_open.hide()
        self.btn_clear.show()
        self.btn_save.setEnabled(False)

    def start_removal_thread(self):
        # Prepare params
        model_name = self.combo_model.currentData()
        use_alpha = self.chk_alpha.isChecked()
        use_post = self.chk_post.isChecked()
        
        status_msg = f"Processing with {self.combo_model.currentText()}..."
        if model_name != "isnet-general-use" and model_name != "u2net": 
             status_msg += " (First run may take time to download)"
        
        self.status_label.setText(status_msg)
        self.progress_bar.show()
        self.result_label.setText("Processing...")
        
        self.btn_open.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.combo_model.setEnabled(False) # Lock controls
        self.chk_alpha.setEnabled(False)
        self.chk_post.setEnabled(False)

        self.worker = Worker(self.original_image, model_name, use_alpha, use_post)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.worker.start()

    def on_processing_finished(self, result_image):
        self.processed_image = result_image
        self.progress_bar.hide()
        self.status_label.setText("Done!")
        self.display_image(self.processed_image, self.result_label)
        self.btn_save.setEnabled(True)
        self.btn_open.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.combo_model.setEnabled(True)
        self.chk_alpha.setEnabled(True)
        self.chk_post.setEnabled(True)

    def on_processing_error(self, error_msg):
        self.progress_bar.hide()
        self.status_label.setText("Error occurred.")
        self.result_label.setText("Failed")
        QMessageBox.critical(self, "Processing Error", error_msg)

    def display_image(self, pil_image, label_widget):
        # PIL to QImage
        im_data = pil_image.convert("RGBA").tobytes("raw", "RGBA")
        qim = QImage(im_data, pil_image.size[0], pil_image.size[1], QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qim)
        
        # Scale to fit label
        scaled_pixmap = pixmap.scaled(
            label_widget.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        label_widget.setPixmap(scaled_pixmap)

    def save_image(self):
        if not self.processed_image:
            return

        initial_name = "output.png"
        if self.current_file_path:
            base = os.path.splitext(os.path.basename(self.current_file_path))[0]
            initial_name = f"{base}_nobg.png"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", initial_name, "PNG Image (*.png)"
        )
        
        if file_path:
            try:
                self.processed_image.save(file_path)
                self.status_label.setText(f"Saved to {file_path}")
                QMessageBox.information(self, "Success", "Image saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save image: {str(e)}")

    def reset_ui(self):
        self.original_image = None
        self.processed_image = None
        self.current_file_path = None
        
        # Remove split view widget
        self.original_label.setParent(None)
        self.result_label.setParent(None)
        
        # Clear specific labels logic to ensure they can be re-added
        self.content_layout.removeWidget(self.original_label)
        self.content_layout.removeWidget(self.result_label)

        # Restore drop label
        self.content_layout.addWidget(self.drop_label)
        
        self.btn_open.show()
        self.btn_clear.hide()
        self.btn_save.setEnabled(False)
        self.status_label.setText("Ready - Drag image or Ctrl+V to paste")
        self.result_label.clear()
        self.original_label.clear()

    def resizeEvent(self, event):
        # Re-scale images on resize if they exist
        if self.original_image and self.original_label.isVisible():
            self.display_image(self.original_image, self.original_label)
        if self.processed_image and self.result_label.isVisible():
            self.display_image(self.processed_image, self.result_label)
        super().resizeEvent(event)

if __name__ == "__main__":
    # Test execution
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
