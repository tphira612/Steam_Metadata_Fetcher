import sys
import os
import glob
import requests
from dotenv import load_dotenv
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QWidget, QPushButton, QLabel, QTextEdit,
                             QHBoxLayout, QGroupBox, QProgressBar,
                             QLineEdit, QMessageBox, QListWidget, 
                             QListWidgetItem, QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv('API_KEY')

class SteamGridDbClient:
    def __init__(self):
        self.base_url = "https://www.steamgriddb.com/api/v2"
        self.api_key = API_KEY
    
    def set_api_key(self, api_key):
        self.api_key = api_key.strip()
    
    def search_game(self, game_name):
        if not self.api_key:
            return {"error": "API key not set. Please retrieve one at https://www.steamgriddb.com/profile/preferences/api"}
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/search/autocomplete/{requests.utils.quote(game_name)}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API request failed: {response.status_code}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

class ScanThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(list)
    
    def __init__(self, scan_type):
        super().__init__()
        self.scan_type = scan_type
    
    def run(self):
        if self.scan_type == "local":
            games = self.scan_local_games()
        elif self.scan_type == "steam":
            games = ["Steam scanning not implemented yet"]
        else:
            games = ["Epic scanning not implemented yet"]
        
        self.finished_signal.emit(games)
    
    def scan_local_games(self):
        self.progress_signal.emit("Scanning for game executables...")
        game_extensions = ['*.exe']
        common_paths = [
            "C:\\Program Files\\*",
            "C:\\Program Files (x86)\\*", 
            os.path.expanduser("~\\Desktop\\*")
        ]
        
        found_games = []
        for path in common_paths:
            for ext in game_extensions:
                search_pattern = os.path.join(path, ext)
                try:
                    files = glob.glob(search_pattern, recursive=True)
                    for file in files[:10]:
                        filename = os.path.basename(file)
                        if any(skip in filename.lower() for skip in ['unins', 'install', 'setup', 'unreal']):
                            continue
                        found_games.append({
                            'name': os.path.splitext(filename)[0],
                            'path': file,
                            'type': 'local'
                        })
                except Exception as e:
                    self.progress_signal.emit(f"Error scanning {path}: {e}")
        
        return found_games[:15]
    def scan_steam_games(self):
    def scan_epic_games(self):

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.steamgrid_client = SteamGridDbClient()
        self.found_games = []
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Steam Metadata Fetcher")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Steam Metadata Fetcher")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # API Key section
        api_group = QGroupBox("SteamGridDB API Configuration")
        api_layout = QHBoxLayout(api_group)
        api_layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your SteamGridDB API key...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_key_input)
        
        self.save_api_btn = QPushButton("Save Key")
        api_layout.addWidget(self.save_api_btn)
        layout.addWidget(api_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Scan section
        scan_group = QGroupBox("Game Detection")
        scan_layout = QHBoxLayout(scan_group)
        
        self.scan_local_btn = QPushButton("Scan Local Games")
        self.scan_steam_btn = QPushButton("Scan Steam Games") 
        self.scan_epic_btn = QPushButton("Scan Epic Games")
        
        scan_layout.addWidget(self.scan_local_btn)
        scan_layout.addWidget(self.scan_steam_btn)
        scan_layout.addWidget(self.scan_epic_btn)
        
        layout.addWidget(scan_group)
        
        # Create splitter for game list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Game list on the left
        self.game_list_widget = QListWidget()
        self.game_list_widget.itemSelectionChanged.connect(self.on_game_selected)
        splitter.addWidget(self.game_list_widget)
        
        # Details area on the right
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        self.details_label = QLabel("Select a game to view details")
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_layout.addWidget(self.details_label)
        
        self.details_text = QTextEdit()
        self.details_text.setPlaceholderText("Game details and metadata will appear here...")
        details_layout.addWidget(self.details_text)
        
        splitter.addWidget(details_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        # Connect buttons
        self.save_api_btn.clicked.connect(self.save_api_key)
        self.scan_local_btn.clicked.connect(lambda: self.start_scan("local"))
        self.scan_steam_btn.clicked.connect(lambda: self.start_scan("steam"))
        self.scan_epic_btn.clicked.connect(lambda: self.start_scan("epic"))
    
    def save_api_key(self):
        api_key = self.api_key_input.text()
        if api_key:
            self.steamgrid_client.set_api_key(api_key)
            self.details_text.append("API key saved successfully!")
        else:
            QMessageBox.warning(self, "Warning", "Please enter an API key")
    
    def start_scan(self, scan_type):
        if scan_type == "local" and not self.steamgrid_client.api_key:
            QMessageBox.warning(self, "API Key Required", 
                               "Please set your SteamGridDB API key first to fetch metadata.")
            return
        
        self.progress_bar.setVisible(True)
        self.game_list_widget.clear()
        self.details_text.clear()
        self.details_text.append(f"Starting {scan_type} game scan...")
        
        self.scan_thread = ScanThread(scan_type)
        self.scan_thread.progress_signal.connect(self.update_progress)
        self.scan_thread.finished_signal.connect(self.scan_finished)
        self.scan_thread.start()
    
    def update_progress(self, message):
        self.details_text.append(message)
    
    def scan_finished(self, games):
        self.progress_bar.setVisible(False)
        self.found_games = games
        self.details_text.append(f"Scan completed! Found {len(games)} games.\\n")
        
        # Populate game list
        for i, game in enumerate(games):
            if isinstance(game, dict):
                item = QListWidgetItem(f"{game['name']} (Local)")
                item.setData(Qt.ItemDataRole.UserRole, i)  # Store index
                self.game_list_widget.addItem(item)
            else:
                item = QListWidgetItem(str(game))
                self.game_list_widget.addItem(item)
    
    def on_game_selected(self):
        selected_items = self.game_list_widget.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        game_index = item.data(Qt.ItemDataRole.UserRole)
        
        if game_index is not None and game_index < len(self.found_games):
            game = self.found_games[game_index]
            if isinstance(game, dict):
                self.show_game_details(game)
    
    def show_game_details(self, game):
        self.details_text.clear()
        self.details_text.append(f"Game: {game['name']}")
        self.details_text.append(f"Path: {game['path']}")
        self.details_text.append(f"Type: {game['type']}")
        self.details_text.append("\\nSearching for metadata...")
        
        # Look up metadata
        self.lookup_game_metadata(game['name'])
    
    def lookup_game_metadata(self, game_name):
        result = self.steamgrid_client.search_game(game_name)
        
        if 'data' in result and result['data']:
            self.details_text.append("\\n🎮 Found matching games:")
            games_found = result['data'][:5]
            for game in games_found:
                self.details_text.append(f"  ✓ {game['name']} (ID: {game.get('id', 'N/A')})")
        elif 'error' in result:
            self.details_text.append(f"\\n❌ Error: {result['error']}")
        else:
            self.details_text.append("\\n❌ No metadata found")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()