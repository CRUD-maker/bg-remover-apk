from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFloatingActionButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.imagelist import MDSmartTile
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock

import os
import shutil
from remover_mobile import MobileRemover
from PIL import Image

class MainScreen(MDScreen):
    pass

class BGRemoverApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        
        # Main Layout
        layout = MDBoxLayout(orientation='vertical')
        
        # Toolbar
        self.toolbar = MDTopAppBar(title="BG Remover AI")
        self.toolbar.right_action_items = [["information", lambda x: self.show_info()]]
        layout.add_widget(self.toolbar)
        
        # Content Area
        self.content = MDBoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Image Card
        self.image_card = MDCard(
            orientation='vertical',
            size_hint=(1, 0.6),
            elevation=2,
            radius=[20,]
        )
        
        # Image Display
        self.image_display = MDSmartTile(
            source="assets/placeholder.png" if os.path.exists("assets/placeholder.png") else "",
            size_hint=(1, 1),
            radius=[20,],
            box_radius=[0, 0, 20, 20]
        )
        self.image_display.add_widget(MDLabel(text="Tap + to Upload", halign="center", theme_text_color="Custom", text_color=(1,1,1,1)))
        self.image_card.add_widget(self.image_display)
        
        self.content.add_widget(self.image_card)
        
        # Status Label
        self.status_label = MDLabel(
            text="Ready",
            halign="center",
            theme_text_color="Secondary",
            size_hint=(1, 0.1)
        )
        self.content.add_widget(self.status_label)
        
        # Actions
        actions = MDBoxLayout(orientation='horizontal', spacing=20, size_hint=(1, 0.1))
        
        self.btn_save = MDRaisedButton(
            text="SAVE RESULT",
            size_hint=(0.5, 1),
            disabled=True
        )
        self.btn_save.bind(on_release=self.save_image)
        
        actions.add_widget(self.btn_save)
        self.content.add_widget(actions)
        
        layout.add_widget(self.content)
        
        # FAB
        self.fab = MDFloatingActionButton(
            icon="plus",
            pos_hint={'center_x': 0.85, 'center_y': 0.1}
        )
        self.fab.bind(on_release=self.file_manager_open)
        layout.add_widget(self.fab)

        # File Manager
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
        )
        
        # Init AI
        self.remover = None # Lazy load
        
        return layout

    def on_start(self):
        # Initialize AI in background to avoid freeze
        pass

    def file_manager_open(self, *args):
        path = os.path.expanduser("~")
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            path = "/storage/emulated/0/"
            
        self.file_manager.show(path)

    def select_path(self, path):
        self.exit_manager()
        self.status_label.text = "Processing..."
        self.image_display.source = path
        
        # Run AI
        if not self.remover:
            self.remover = MobileRemover()
            
        try:
            # Process
            output = self.remover.process_image(path)
            self.current_result = output
            
            # Save temp preview
            temp_path = "temp_result.png"
            output.save(temp_path)
            self.image_display.source = temp_path
            self.image_display.reload()
            
            self.status_label.text = "Background Removed!"
            self.btn_save.disabled = False
            
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"

    def exit_manager(self, *args):
        self.file_manager.close()

    def save_image(self, *args):
        if platform == 'android':
            from android.storage import primary_external_storage_path
            dir = primary_external_storage_path()
            download_dir = os.path.join(dir, 'Download')
            filename = f"nobg_{int(Clock.get_time())}.png"
            save_path = os.path.join(download_dir, filename)
            self.current_result.save(save_path)
            self.status_label.text = f"Saved to Downloads/{filename}"
        else:
            self.current_result.save("output_mobile.png")
            self.status_label.text = "Saved to output_mobile.png"

    def show_info(self):
        d = MDDialog(title="About", text="AI Background Remover\n\nDeveloped by Faseeh Ansari\nPowered by U2-Net")
        d.open()

if __name__ == "__main__":
    BGRemoverApp().run()
