# Update Steam_Metadata_Fetcher.py with basic API client
import sys
import os
import glob
import requests
from dotenv import load_dotenv
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QWidget, QPushButton, QLabel, QTextEdit,
                             QHBoxLayout, QGroupBox, QProgressBar,
                             QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Load environment variables from .env file
load_dotenv()  # Load variables from .env file
API_KEY = os.getenv('API_KEY')  # Get the API key from environment variables

"""Main Client"""
class SteamGridDbClient:
    def __init__(self):
        self.base_url = "https://www.steamgriddb.com/api/v2"
        self.api_key = API_KEY
    
    def set_api_key(self, api_key):
        """Set the API key for authentication"""
        self.api_key = api_key.strip()
    
    def search_game(self, game_name):
        """Search for a game by name"""
        if not self.api_key:
            return {"error": "API key not set"}
        
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
    """Thread for scanning games to prevent UI freezing"""
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
                    for file in files[:10]:  # Limit for testing
                        # Filter out system files
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
        
        return found_games[:15]  # Limit results for testing

class GameScanner:
    def __init__(self):
        self.scan_thread = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.scanner = GameScanner()
        self.steamgrid_client = SteamGridDbClient()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Steam Metadata Fetcher")
        self.setGeometry(100, 100, 1000, 800)
        
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
        
        # Results area
        self.output_area = QTextEdit()
        self.output_area.setPlaceholderText("Discovered games and metadata will appear here...")
        layout.addWidget(self.output_area)
        
        # Connect buttons
        self.save_api_btn.clicked.connect(self.save_api_key)
        self.scan_local_btn.clicked.connect(lambda: self.start_scan("local"))
        self.scan_steam_btn.clicked.connect(lambda: self.start_scan("steam"))
        self.scan_epic_btn.clicked.connect(lambda: self.start_scan("epic"))
    
    def save_api_key(self):
        api_key = self.api_key_input.text()
        if api_key:
            self.steamgrid_client.set_api_key(api_key)
            self.output_area.append("API key saved successfully!")
        else:
            QMessageBox.warning(self, "Warning", "Please enter an API key")
    
    def start_scan(self, scan_type):
        if scan_type == "local" and not self.steamgrid_client.api_key:
            QMessageBox.warning(self, "API Key Required", 
                               "Please set your SteamGridDB API key first to fetch metadata.")
            return
        
        self.progress_bar.setVisible(True)
        self.output_area.append(f"Starting {scan_type} game scan...")
        
        self.scan_thread = ScanThread(scan_type)
        self.scan_thread.progress_signal.connect(self.update_progress)
        self.scan_thread.finished_signal.connect(self.scan_finished)
        self.scan_thread.start()
    
    def update_progress(self, message):
        self.output_area.append(message)
    
    def scan_finished(self, games):
        self.progress_bar.setVisible(False)
        self.output_area.append("Scan completed! Found games:\\n")
        
        for game in games:
            if isinstance(game, dict):
                self.output_area.append(f"  - {game['name']} (Local)")
                # Try to find metadata for this game
                self.lookup_game_metadata(game['name'])
            else:
                self.output_area.append(f"  - {game}")
        
        self.output_area.append("")  # Empty line
    
    def lookup_game_metadata(self, game_name):
        """Look up game metadata using SteamGridDB"""
        self.output_area.append(f"    Searching metadata for: {game_name}")
        result = self.steamgrid_client.search_game(game_name)
        
        if 'data' in result and result['data']:
            games_found = result['data'][:3]  # Show first 3 results
            for game in games_found:
                self.output_area.append(f"      ✓ {game['name']} (ID: {game.get('id', 'N/A')})")
        elif 'error' in result:
            self.output_area.append(f"      ✗ Error: {result['error']}")
        else:
            self.output_area.append("      ✗ No metadata found")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()