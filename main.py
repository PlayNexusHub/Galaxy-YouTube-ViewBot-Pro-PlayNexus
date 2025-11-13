import sys
import threading
import time
import os
import json
import random
import urllib.request
import traceback
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QStackedLayout, QFrame,
    QFileDialog, QMessageBox, QSpinBox, QCheckBox, QGroupBox, QProgressBar,
    QDateTimeEdit, QTableWidget, QTableWidgetItem, QScrollArea, QComboBox,
    QSlider, QTabWidget, QSplitter, QHeaderView, QCalendarWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer, QDateTime, QDate, QTime
from PyQt5.QtGui import QMovie, QFont, QTextCursor, QIcon, QColor, QPalette, QLinearGradient, QBrush
import undetected_chromedriver as uc

# --- 100X UPGRADE: Utility imports ---
import platform
import psutil
import socket

# --- 100X UPGRADE: Helper for async tasks ---
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import csv
import re
from collections import deque

# --- 100X UPGRADE: Global constants ---
APP_NAME = "🌌 Galaxy YouTube ViewBot Pro 🌌"

# Load version from version.json
try:
    import json
    with open('version.json', 'r') as f:
        version_data = json.load(f)
        APP_VERSION = f"v{version_data.get('version', '3.1.0')}"
except:
    APP_VERSION = "v3.1.0"

MAX_HISTORY = 100
MAX_QUEUE = 500
MAX_THREADS = 200

class WorkerSignals(QObject):
    log = pyqtSignal(str)
    stats_update = pyqtSignal(dict)
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    video_analytics = pyqtSignal(dict)
    scheduler_triggered = pyqtSignal(str)

class YouTubeViewBot(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION} - 10X UPGRADE")
        self.setGeometry(100, 60, 1400, 900)
        self.setWindowIcon(QIcon("galaxy.gif") if os.path.exists("galaxy.gif") else QIcon())

        # App state
        self.running = False
        self.threads = []
        self.executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
        self.view_count = 0
        self.error_count = 0
        self.watch_time = 15
        self.view_delay = 2
        self.headless_mode = True
        self.incognito_mode = True
        self.rotate_proxies = False
        self.proxy = None
        self.user_agents = [
            # List of popular user agents for spoofing
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 Mobile Safari/537.36"
        ]
        self.url_history = []
        self.multi_video_queue = []
        self.proxy_pool = []
        self.active_threads = 0
        self.max_concurrent_views = 5

        # Settings
        self.clear_cache = True
        self.clear_cookies = True
        self.random_watch_time = True
        self.random_delay = True
        self.auto_like = True
        self.auto_subscribe = True
        self.minimize_window = False
        self.mute_audio = True
        self.auto_comment_enabled = False
        self.comment_text = "Nice video! 🚀"
        self.save_logs_on_exit = True

        # 10X UPGRADE: Advanced stats and analytics
        self.cpu_usage = 0
        self.ram_usage = 0
        self.network_usage = 0
        self.last_stats_update = time.time()
        
        # Analytics tracking
        self.analytics_data = {
            'views_per_hour': deque(maxlen=60),
            'views_per_day': {},
            'success_rate_history': deque(maxlen=100),
            'video_analytics': [],
            'performance_metrics': deque(maxlen=100)
        }
        
        # Scheduler
        self.scheduled_tasks = []
        self.scheduler_running = False
        
        # AI Comment templates
        self.comment_templates = [
            "Great video! Really enjoyed it! 🚀",
            "Amazing content! Keep it up! 💯",
            "This is exactly what I needed! Thanks! 👍",
            "Awesome work! Subscribed! ⭐",
            "Love your content! More please! 🔥",
            "Very informative! Learned a lot! 📚",
            "Best video on this topic! 🎯",
            "You deserve more views! Keep going! 💪"
        ]
        
        # Video analytics cache
        self.video_cache = {}
        
        # Statistics tracking
        self.total_views_today = 0
        self.total_views_week = 0
        self.total_views_month = 0
        self.start_time = time.time()
        self.session_start = datetime.now()

        self.signals = WorkerSignals()
        self.signals.log.connect(self.log)
        self.signals.stats_update.connect(self.update_stats)
        self.signals.progress.connect(self.update_progress)
        self.signals.finished.connect(self.on_thread_finished)
        self.signals.video_analytics.connect(self.update_video_analytics)
        self.signals.scheduler_triggered.connect(self.handle_scheduled_task)

        self.init_ui()
        self.init_timers()

    def init_ui(self):
        # 10X UPGRADE: Modern UI Design
        self.setStyleSheet("""
            QWidget {
                background-color: #0a0e27;
                color: #00d9ff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a3a5c, stop:1 #0d1f3d);
                border: 2px solid #00d9ff;
                border-radius: 8px;
                color: #00d9ff;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                min-height: 35px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a5a7c, stop:1 #1d3f5d);
                border-color: #00ffff;
                color: #00ffff;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0d1f3d, stop:1 #1a3a5c);
            }
            QLineEdit, QTextEdit {
                background-color: #1a1a2e;
                border: 2px solid #16213e;
                border-radius: 6px;
                color: #00d9ff;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #00d9ff;
                background-color: #1a1a3e;
            }
            QListWidget {
                background-color: #1a1a2e;
                border: 2px solid #16213e;
                border-radius: 6px;
                color: #00d9ff;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #16213e;
            }
            QListWidget::item:selected {
                background-color: #00d9ff;
                color: #0a0e27;
            }
            QListWidget::item:hover {
                background-color: #16213e;
            }
            QGroupBox {
                border: 2px solid #00d9ff;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: #00d9ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QProgressBar {
                border: 2px solid #16213e;
                border-radius: 6px;
                text-align: center;
                color: #00d9ff;
                background-color: #1a1a2e;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d9ff, stop:1 #00ffff);
                border-radius: 4px;
            }
            QCheckBox {
                color: #00d9ff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #00d9ff;
                border-radius: 4px;
                background-color: #1a1a2e;
            }
            QCheckBox::indicator:checked {
                background-color: #00d9ff;
                border-color: #00ffff;
            }
            QSpinBox {
                background-color: #1a1a2e;
                border: 2px solid #16213e;
                border-radius: 6px;
                color: #00d9ff;
                padding: 5px;
            }
            QTabWidget::pane {
                border: 2px solid #16213e;
                border-radius: 6px;
                background-color: rgba(26, 26, 46, 0.9);
            }
        """)

        # Background galaxy GIF
        bg = QLabel(self)
        if os.path.exists("galaxy.gif"):
            movie = QMovie("galaxy.gif")
            bg.setMovie(movie)
            movie.start()
        else:
            bg.setText("🌌")
        bg.setScaledContents(True)
        bg.setGeometry(0, 0, 1400, 900)
        bg.lower()

        main_layout = QHBoxLayout(self)
        self.setLayout(main_layout)

        # Side tabs list
        self.tab_list = QListWidget()
        self.tab_list.setFixedWidth(240)
        self.tab_list.setStyleSheet("""
            QListWidget {background-color: #111;}
            QListWidget::item {padding: 18px; font-size: 15pt;}
            QListWidget::item:selected {background-color: #222; color: #00ffe7;}
        """)
        tabs = [
            "🎯 Control Panel",
            "🛠️ Functions",
            "📊 Analytics",
            "📅 Scheduler",
            "🎥 Video Tools",
            "🧠 AI Assistant",
            "⚙️ Settings",
            "❓ Help"
        ]
        for tab_name in tabs:
            item = QListWidgetItem(tab_name)
            item.setFont(QFont("Consolas", 15))
            self.tab_list.addItem(item)
        self.tab_list.currentRowChanged.connect(self.display_tab)
        main_layout.addWidget(self.tab_list)

        # Stacked layout for tabs content
        self.stack = QStackedLayout()
        main_layout.addLayout(self.stack)

        # Tab 0: ViewBot Control
        self.tab_viewbot = QFrame()
        self.tab_viewbot.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        self.stack.addWidget(self.tab_viewbot)
        self.init_tab_viewbot()

        # Tab 1: Functions
        self.tab_functions = QFrame()
        self.tab_functions.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        self.stack.addWidget(self.tab_functions)
        self.init_tab_functions()

        # Tab 2: Analytics (renamed from Stats)
        self.tab_stats = QFrame()
        self.tab_stats.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        self.stack.addWidget(self.tab_stats)
        self.init_tab_stats()

        # Tab 3: Scheduler (NEW)
        self.tab_scheduler = QFrame()
        self.tab_scheduler.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        self.stack.addWidget(self.tab_scheduler)
        self.init_tab_scheduler()
        
        # Tab 4: Video Tools (NEW)
        self.tab_video_tools = QFrame()
        self.tab_video_tools.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        self.stack.addWidget(self.tab_video_tools)
        self.init_tab_video_tools()
        
        # Tab 5: AI Assistant
        self.tab_ai = QFrame()
        self.tab_ai.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        self.stack.addWidget(self.tab_ai)
        self.init_tab_ai_tools()

        # Tab 6: Settings
        self.tab_settings = QFrame()
        self.tab_settings.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        self.stack.addWidget(self.tab_settings)
        self.init_tab_settings()

        # Tab 7: Help
        self.tab_help = QFrame()
        self.tab_help.setStyleSheet("background-color: rgba(0,0,0,0.7);")
        self.stack.addWidget(self.tab_help)
        self.init_tab_help()

        self.tab_list.setCurrentRow(0)

    def init_timers(self):
        # 10X UPGRADE: Enhanced timers
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_resource_stats)
        self.stats_timer.start(2000)
        
        # Analytics update timer
        self.analytics_timer = QTimer(self)
        self.analytics_timer.timeout.connect(self.update_analytics)
        self.analytics_timer.start(5000)
        
        # Scheduler timer
        self.scheduler_timer = QTimer(self)
        self.scheduler_timer.timeout.connect(self.check_scheduled_tasks)
        self.scheduler_timer.start(60000)  # Check every minute

    def display_tab(self, index):
        self.stack.setCurrentIndex(index)

    ##########################
    # Tab 0: ViewBot Control
    def init_tab_viewbot(self):
        layout = QVBoxLayout()
        self.tab_viewbot.setLayout(layout)

        title = QLabel("🚀 Galaxy YouTube ViewBot Ultra X Control Panel")
        title.setFont(QFont("Consolas", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube Video URL here")
        self.url_input.setStyleSheet("background-color: #222; color: white; padding: 12px; font-size:15px;")
        layout.addWidget(self.url_input)

        btn_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶️ Start Bot")
        self.start_btn.clicked.connect(self.start_bot)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹️ Stop Bot")
        self.stop_btn.clicked.connect(self.stop_bot)
        btn_layout.addWidget(self.stop_btn)

        self.next_btn = QPushButton("⏭️ Play Next URL")
        self.next_btn.clicked.connect(self.play_next_url)
        btn_layout.addWidget(self.next_btn)

        self.mass_start_btn = QPushButton("💥 Mass Start (All Queue)")
        self.mass_start_btn.clicked.connect(self.mass_start)
        btn_layout.addWidget(self.mass_start_btn)

        layout.addLayout(btn_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {background-color: #222; color: #00ffe7; border: 1px solid #00ffe7;}
            QProgressBar::chunk {background-color: #00ffe7;}
        """)
        layout.addWidget(self.progress_bar)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("""
            background-color: #111;
            color: #00ff00;
            font-family: Consolas;
            font-size: 13px;
        """)
        layout.addWidget(self.log_box)

    def log(self, msg):
        timestamp = time.strftime('%H:%M:%S')
        self.log_box.append(f"[{timestamp}] {msg}")
        self.log_box.moveCursor(QTextCursor.End)

    def update_stats(self, stats):
        stats_str = (
            f"Views Completed: {stats.get('views', self.view_count)}\n"
            f"Errors: {stats.get('errors', self.error_count)}\n"
            f"Running: {'Yes' if self.running else 'No'}\n"
            f"Active Threads: {self.active_threads}\n"
            f"CPU: {self.cpu_usage:.1f}%  RAM: {self.ram_usage:.1f}%"
        )
        self.stats_text.setText(stats_str)

    def update_progress(self, val):
        self.progress_bar.setValue(val)

    def on_thread_finished(self):
        self.active_threads = max(0, self.active_threads - 1)
        self.update_stats({})

    def start_bot(self):
        url = self.url_input.text().strip()
        if not url.startswith("http"):
            self.log("⚠️ Invalid URL.")
            return
        if self.running:
            self.log("⚠️ Bot is already running.")
            return
        self.running = True
        self.active_threads += 1

        # Save to history and queue
        self.add_to_url_history(url)
        if url not in self.multi_video_queue:
            self.multi_video_queue.append(url)
            self.queue_list.addItem(url)

        self.log("✅ Starting bot...")
        t = threading.Thread(target=self.view_loop, args=(url,), daemon=True)
        self.threads.append(t)
        t.start()

    def stop_bot(self):
        if not self.running:
            self.log("⚠️ Bot is not running.")
            return
        self.running = False
        self.log("🛑 Bot stopped.")

    def play_next_url(self):
        if self.running:
            self.log("⚠️ Stop current bot first.")
            return
        if not self.multi_video_queue:
            self.log("⚠️ No URLs in queue.")
            return
        next_url = self.multi_video_queue.pop(0)
        self.url_input.setText(next_url)
        self.start_bot()

    def mass_start(self):
        if self.running:
            self.log("⚠️ Bot is already running.")
            return
        if not self.multi_video_queue:
            self.log("⚠️ No URLs in queue.")
            return
        self.running = True
        self.active_threads = 0
        self.log(f"💥 Mass starting {len(self.multi_video_queue)} videos with {self.max_concurrent_views} threads...")
        for i, url in enumerate(self.multi_video_queue[:self.max_concurrent_views]):
            t = threading.Thread(target=self.view_loop, args=(url,), daemon=True)
            self.threads.append(t)
            self.active_threads += 1
            t.start()

    def add_to_url_history(self, url):
        if url in self.url_history:
            self.url_history.remove(url)
        self.url_history.insert(0, url)
        if len(self.url_history) > MAX_HISTORY:
            self.url_history.pop()
        self.update_url_history()

    def get_random_user_agent(self):
        return random.choice(self.user_agents)

    def view_loop(self, url):
        count = 0
        try:
            while self.running:
                try:
                    self.signals.log.emit("🔁 Launching browser instance...")

                    options = uc.ChromeOptions()

                    # User agent spoofing
                    ua = self.get_random_user_agent()
                    options.add_argument(f"user-agent={ua}")

                    # Proxy support with rotation
                    if self.rotate_proxies and self.proxy_list.count() > 0:
                        proxies = [self.proxy_list.item(i).text() for i in range(self.proxy_list.count())]
                        proxy = random.choice(proxies)
                        options.add_argument(f'--proxy-server={proxy}')
                        self.log(f"🔒 Using proxy: {proxy}")
                    elif self.proxy:
                        options.add_argument(f'--proxy-server={self.proxy}')

                    # Browser mode settings
                    if self.headless_mode:
                        options.add_argument("--headless=new")
                    if self.incognito_mode:
                        options.add_argument("--incognito")

                    # Common performance flags
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-notifications")
                    options.add_argument("--disable-popup-blocking")
                    options.add_argument("--disable-translate")
                    options.add_argument("--disable-extensions")
                    options.add_argument("--log-level=3")

                    # Audio settings
                    if self.mute_audio:
                        options.add_argument("--mute-audio")

                    driver = uc.Chrome(options=options)
                    driver.get(url)
                    self.signals.log.emit(f"🌐 Navigated to {url}")
                    time.sleep(3)

                    # Feature: Video Info Scraper
                    info = self.scrape_video_info(driver)
                    self.signals.log.emit(f"🎥 Video Title: {info.get('title', 'N/A')}")
                    self.signals.log.emit(f"👁️ Views: {info.get('views', 'N/A')}")
                    self.signals.log.emit(f"👍 Likes: {info.get('likes', 'N/A')}")

                    # Feature: Detect Live Stream
                    is_live = self.detect_live_stream(driver)
                    self.signals.log.emit(f"🔴 Live Stream Detected: {'Yes' if is_live else 'No'}")

                    # Feature: Video Duration
                    duration = self.get_video_duration(driver)
                    self.signals.log.emit(f"⏰ Duration: {duration}")

                    # Randomize watch time if enabled
                    if self.random_watch_time:
                        watch_time = random.randint(int(self.watch_time * 0.8), int(self.watch_time * 1.2))
                        self.signals.log.emit(f"🎲 Randomized watch time: {watch_time} seconds")
                    else:
                        watch_time = self.watch_time

                    # Watch video
                    self.signals.log.emit(f"👀 Watching video for {watch_time} seconds...")
                    for i in range(watch_time):
                        if not self.running:
                            break
                        time.sleep(1)
                        self.signals.progress.emit(int((i+1)/watch_time*100))

                    # Auto actions if enabled
                    if self.auto_like:
                        self.auto_click_like(driver)
                    
                    if self.auto_subscribe:
                        self.auto_subscribe_channel(driver)

                    # Auto-comment (if enabled)
                    if self.auto_comment_enabled:
                        self.auto_comment(driver, self.comment_text)

                    # Minimize window if enabled
                    if self.minimize_window:
                        driver.minimize_window()

                    driver.quit()
                    count += 1
                    self.view_count += 1
                    self.total_views_today += 1
                    # Update weekly/monthly stats
                    days_since_start = (datetime.now() - self.session_start).days
                    if days_since_start < 7:
                        self.total_views_week += 1
                    if days_since_start < 30:
                        self.total_views_month += 1
                    self.signals.log.emit(f"✅ View #{count} completed.")
                    self.signals.stats_update.emit({"views": self.view_count, "errors": self.error_count})

                    # Randomize delay if enabled
                    if self.random_delay:
                        delay = random.randint(int(self.view_delay * 0.8), int(self.view_delay * 1.2))
                        self.signals.log.emit(f"🎲 Randomized delay: {delay} seconds")
                        for i in range(delay):
                            if not self.running:
                                break
                            time.sleep(1)
                    else:
                        time.sleep(self.view_delay)
                except Exception as e:
                    self.error_count += 1
                    self.signals.log.emit(f"❌ Error: {str(e)}\n{traceback.format_exc()}")
                    self.signals.stats_update.emit({"views": self.view_count, "errors": self.error_count})
                    time.sleep(3)
        finally:
            self.signals.finished.emit()

    ##########################
    # Tab 1: Functions (UI + backend)

    def init_tab_functions(self):
        layout = QVBoxLayout()
        self.tab_functions.setLayout(layout)

        title = QLabel("🛠️ YouTube Utilities & Queue")
        title.setFont(QFont("Consolas", 19, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Advanced Settings Group
        settings_group = QGroupBox("🛠️ Advanced Settings")
        settings_layout = QVBoxLayout()
        
        # Watch Time and Delay Controls
        time_layout = QHBoxLayout()
        self.watch_time_spin = QSpinBox()
        self.watch_time_spin.setMinimum(5)
        self.watch_time_spin.setMaximum(600)
        self.watch_time_spin.setValue(self.watch_time)
        self.watch_time_spin.setPrefix("Watch Time: ")
        self.watch_time_spin.setSuffix(" sec")
        self.watch_time_spin.valueChanged.connect(self.set_watch_time)
        time_layout.addWidget(self.watch_time_spin)

        self.view_delay_spin = QSpinBox()
        self.view_delay_spin.setMinimum(0)
        self.view_delay_spin.setMaximum(120)
        self.view_delay_spin.setValue(self.view_delay)
        self.view_delay_spin.setPrefix("Delay: ")
        self.view_delay_spin.setSuffix(" sec")
        self.view_delay_spin.valueChanged.connect(self.set_view_delay)
        time_layout.addWidget(self.view_delay_spin)
        settings_layout.addLayout(time_layout)

        # Browser Settings
        browser_layout = QHBoxLayout()
        self.headless_checkbox = QCheckBox("Headless Mode")
        self.headless_checkbox.setChecked(self.headless_mode)
        self.headless_checkbox.stateChanged.connect(self.toggle_headless_mode)
        browser_layout.addWidget(self.headless_checkbox)

        self.incognito_checkbox = QCheckBox("Incognito Mode")
        self.incognito_checkbox.setChecked(self.incognito_mode)
        self.incognito_checkbox.stateChanged.connect(self.toggle_incognito_mode)
        browser_layout.addWidget(self.incognito_checkbox)
        settings_layout.addLayout(browser_layout)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Video Queue Management
        queue_group = QGroupBox("📋 Video Queue Management")
        queue_layout = QVBoxLayout()

        # Add URL Button
        self.add_url_btn = QPushButton("➕ Add URL to Queue")
        self.add_url_btn.clicked.connect(self.add_url_to_queue)
        queue_layout.addWidget(self.add_url_btn)

        # Queue List
        self.queue_list = QListWidget()
        self.queue_list.setStyleSheet("""
            QListWidget {background-color: #111;}
            QListWidget::item {padding: 10px; font-size: 14px;}
            QListWidget::item:selected {background-color: #222; color: #00ffe7;}
        """)
        queue_layout.addWidget(self.queue_list)

        # Queue Controls
        queue_controls = QHBoxLayout()
        self.clear_queue_btn = QPushButton("🗑️ Clear Queue")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        queue_controls.addWidget(self.clear_queue_btn)

        self.save_queue_btn = QPushButton("💾 Save Queue")
        self.save_queue_btn.clicked.connect(self.save_queue)
        queue_controls.addWidget(self.save_queue_btn)

        self.load_queue_btn = QPushButton("📂 Load Queue")
        self.load_queue_btn.clicked.connect(self.load_queue)
        queue_controls.addWidget(self.load_queue_btn)
        queue_layout.addLayout(queue_controls)

        queue_group.setLayout(queue_layout)
        layout.addWidget(queue_group)

        # Proxy Configuration
        proxy_group = QGroupBox("🔒 Proxy Configuration")
        proxy_layout = QVBoxLayout()

        # Proxy Input
        proxy_input_layout = QHBoxLayout()
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("Enter proxy (http://ip:port or socks5://ip:port)")
        self.proxy_input.setStyleSheet("background-color: #222; color: white; padding: 5px;")
        proxy_input_layout.addWidget(self.proxy_input)

        self.proxy_apply_btn = QPushButton("Apply Proxy")
        self.proxy_apply_btn.clicked.connect(self.apply_proxy)
        proxy_input_layout.addWidget(self.proxy_apply_btn)

        self.proxy_clear_btn = QPushButton("Clear Proxy")
        self.proxy_clear_btn.clicked.connect(self.clear_proxy)
        proxy_input_layout.addWidget(self.proxy_clear_btn)
        proxy_layout.addLayout(proxy_input_layout)

        # Proxy List
        self.proxy_list = QListWidget()
        self.proxy_list.setStyleSheet("""
            QListWidget {background-color: #111;}
            QListWidget::item {padding: 10px; font-size: 14px;}
            QListWidget::item:selected {background-color: #222; color: #00ffe7;}
        """)
        proxy_layout.addWidget(self.proxy_list)

        # Proxy Controls
        proxy_controls = QHBoxLayout()
        self.add_proxy_btn = QPushButton("➕ Add Proxy")
        self.add_proxy_btn.clicked.connect(self.add_proxy)
        proxy_controls.addWidget(self.add_proxy_btn)

        self.remove_proxy_btn = QPushButton("➖ Remove Selected Proxy")
        self.remove_proxy_btn.clicked.connect(self.remove_selected_proxy)
        proxy_controls.addWidget(self.remove_proxy_btn)

        self.rotate_proxy_btn = QPushButton("🔄 Rotate Proxies")
        self.rotate_proxy_btn.clicked.connect(self.toggle_proxy_rotation)
        proxy_controls.addWidget(self.rotate_proxy_btn)
        proxy_layout.addLayout(proxy_controls)

        proxy_group.setLayout(proxy_layout)
        layout.addWidget(proxy_group)

        # User Agent Management
        ua_group = QGroupBox("🤖 User Agent Management")
        ua_layout = QVBoxLayout()

        self.ua_text = QTextEdit()
        self.ua_text.setPlainText("\n".join(self.user_agents))
        ua_layout.addWidget(self.ua_text)

        self.ua_apply_btn = QPushButton("Apply User Agents")
        self.ua_apply_btn.clicked.connect(self.apply_user_agents)
        ua_layout.addWidget(self.ua_apply_btn)

        ua_group.setLayout(ua_layout)
        layout.addWidget(ua_group)

        # URL History
        hist_group = QGroupBox("📜 URL History")
        hist_layout = QVBoxLayout()

        self.history_list = QListWidget()
        hist_layout.addWidget(self.history_list)
        self.update_url_history()

        hist_controls = QHBoxLayout()
        self.clear_history_btn = QPushButton("🗑️ Clear History")
        self.clear_history_btn.clicked.connect(self.clear_history)
        hist_controls.addWidget(self.clear_history_btn)

        self.export_history_btn = QPushButton("💾 Export History")
        self.export_history_btn.clicked.connect(self.export_history)
        hist_controls.addWidget(self.export_history_btn)
        hist_layout.addLayout(hist_controls)

        hist_group.setLayout(hist_layout)
        layout.addWidget(hist_group)

        # Export Logs
        self.export_logs_btn = QPushButton("📄 Export Logs")
        self.export_logs_btn.clicked.connect(self.export_logs)
        layout.addWidget(self.export_logs_btn)

    def set_watch_time(self, val):
        self.watch_time = val
        self.log(f"⚙️ Watch time set to {val} seconds")

    def set_view_delay(self, val):
        self.view_delay = val
        self.log(f"⚙️ Delay between views set to {val} seconds")

    def toggle_headless_mode(self, state):
        self.headless_mode = state == Qt.Checked
        self.log(f"⚙️ Headless mode {'enabled' if self.headless_mode else 'disabled'}")

    def toggle_incognito_mode(self, state):
        self.incognito_mode = state == Qt.Checked
        self.log(f"⚙️ Incognito mode {'enabled' if self.incognito_mode else 'disabled'}")

    def add_url_to_queue(self):
        url = self.url_input.text().strip()
        if not url.startswith("http"):
            self.log("⚠️ Invalid URL.")
            return
        if url not in self.multi_video_queue:
            self.multi_video_queue.append(url)
            self.queue_list.addItem(url)
            self.log(f"✅ Added {url} to queue")
        else:
            self.log("ℹ️ URL already in queue.")

    def clear_queue(self):
        self.multi_video_queue.clear()
        self.queue_list.clear()
        self.log("🗑️ Queue cleared")

    def save_queue(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Queue", "", "Text Files (*.txt)")
        if fname:
            try:
                with open(fname, "w", encoding="utf-8") as f:
                    for url in self.multi_video_queue:
                        f.write(url + "\n")
                self.log(f"💾 Queue saved to {fname}")
            except Exception as e:
                self.log(f"❌ Failed to save queue: {e}")

    def load_queue(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Load Queue", "", "Text Files (*.txt)")
        if fname:
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    urls = [line.strip() for line in f if line.strip()]
                    for url in urls:
                        if url not in self.multi_video_queue:
                            self.multi_video_queue.append(url)
                            self.queue_list.addItem(url)
                self.log(f"📂 Loaded {len(urls)} URLs from {fname}")
            except Exception as e:
                self.log(f"❌ Failed to load queue: {e}")

    def apply_proxy(self):
        p = self.proxy_input.text().strip()
        if p:
            self.proxy = p
            self.log(f"⚙️ Proxy set to {p}")
        else:
            self.log("⚠️ Proxy input empty")

    def clear_proxy(self):
        self.proxy = None
        self.proxy_input.clear()
        self.log("⚙️ Proxy cleared")

    def apply_user_agents(self):
        uas = self.ua_text.toPlainText().strip().splitlines()
        self.user_agents = [ua.strip() for ua in uas if ua.strip()]
        self.log(f"⚙️ Applied {len(self.user_agents)} user agents")

    def update_url_history(self):
        self.history_list.clear()
        for url in self.url_history:
            self.history_list.addItem(url)

    def add_proxy(self):
        proxy_text = self.proxy_input.text().strip()
        if proxy_text:
            self.proxy_list.addItem(proxy_text)
            self.log(f"➕ Added proxy: {proxy_text}")
            self.proxy_input.clear()
        else:
            self.log("⚠️ Proxy input is empty.")

    def remove_selected_proxy(self):
        selected = self.proxy_list.currentRow()
        if selected >= 0:
            proxy = self.proxy_list.item(selected).text()
            self.proxy_list.takeItem(selected)
            self.log(f"➖ Removed proxy: {proxy}")
        else:
            self.log("⚠️ No proxy selected.")

    def toggle_proxy_rotation(self):
        self.rotate_proxies = not self.rotate_proxies
        self.log(f"🔄 Proxy rotation {'enabled' if self.rotate_proxies else 'disabled'}")

    def export_logs(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Logs", "", "Text Files (*.txt)")
        if fname:
            try:
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(self.log_box.toPlainText())
                self.log(f"✅ Logs exported to {fname}")
            except Exception as e:
                self.log(f"❌ Failed to export logs: {e}")

    def clear_history(self):
        self.url_history.clear()
        self.update_url_history()
        self.log("🗑️ History cleared")

    def export_history(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Export History", "", "Text Files (*.txt)")
        if fname:
            try:
                with open(fname, "w", encoding="utf-8") as f:
                    for url in self.url_history:
                        f.write(url + "\n")
                self.log(f"💾 History exported to {fname}")
            except Exception as e:
                self.log(f"❌ Failed to export history: {e}")

    ##########################
    # Tab 2: Analytics Dashboard (10X UPGRADE)
    def init_tab_stats(self):
        layout = QVBoxLayout()
        self.tab_stats.setLayout(layout)

        title = QLabel("📊 Advanced Analytics Dashboard")
        title.setFont(QFont("Consolas", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Stats Grid
        stats_grid = QHBoxLayout()
        
        # Real-time Stats Cards
        stats_card1 = QGroupBox("📈 Performance Metrics")
        stats_layout1 = QVBoxLayout()
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        self.stats_text.setStyleSheet("""
            background-color: #1a1a2e;
            color: #00ff00;
            font-family: Consolas;
            font-size: 14px;
            border: 1px solid #16213e;
        """)
        stats_layout1.addWidget(self.stats_text)
        stats_card1.setLayout(stats_layout1)
        stats_grid.addWidget(stats_card1)
        
        stats_card2 = QGroupBox("💻 System Resources")
        stats_layout2 = QVBoxLayout()
        self.system_stats_text = QTextEdit()
        self.system_stats_text.setReadOnly(True)
        self.system_stats_text.setMaximumHeight(200)
        self.system_stats_text.setStyleSheet("""
            background-color: #1a1a2e;
            color: #00d9ff;
            font-family: Consolas;
            font-size: 14px;
            border: 1px solid #16213e;
        """)
        stats_layout2.addWidget(self.system_stats_text)
        stats_card2.setLayout(stats_layout2)
        stats_grid.addWidget(stats_card2)
        
        layout.addLayout(stats_grid)
        
        # Analytics Table
        analytics_group = QGroupBox("📋 Detailed Analytics")
        analytics_layout = QVBoxLayout()
        self.analytics_table = QTableWidget()
        self.analytics_table.setColumnCount(6)
        self.analytics_table.setHorizontalHeaderLabels([
            "Time", "Views", "Success Rate", "Avg Watch Time", "Errors", "Status"
        ])
        self.analytics_table.horizontalHeader().setStretchLastSection(True)
        self.analytics_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                color: #00d9ff;
                gridline-color: #16213e;
            }
            QHeaderView::section {
                background-color: #0d1f3d;
                color: #00d9ff;
                padding: 8px;
                border: 1px solid #16213e;
                font-weight: bold;
            }
        """)
        analytics_layout.addWidget(self.analytics_table)
        analytics_group.setLayout(analytics_layout)
        layout.addWidget(analytics_group)
        
        # Export Analytics Button
        export_btn = QPushButton("💾 Export Analytics Data")
        export_btn.clicked.connect(self.export_analytics)
        layout.addWidget(export_btn)
        
        self.update_stats({})

    def update_resource_stats(self):
        try:
            self.cpu_usage = psutil.cpu_percent()
            self.ram_usage = psutil.virtual_memory().percent
            self.network_usage = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            
            # Update system stats display
            if hasattr(self, 'system_stats_text'):
                system_info = f"""CPU Usage: {self.cpu_usage:.1f}%
RAM Usage: {self.ram_usage:.1f}%
Network: {self.network_usage / 1024 / 1024:.2f} MB
Active Threads: {self.active_threads}
Uptime: {str(timedelta(seconds=int(time.time() - self.start_time)))}"""
                self.system_stats_text.setText(system_info)
            
            self.update_stats({})
        except Exception:
            pass
    
    def update_analytics(self):
        """10X UPGRADE: Update analytics data"""
        try:
            # Calculate success rate
            total_attempts = self.view_count + self.error_count
            success_rate = (self.view_count / total_attempts * 100) if total_attempts > 0 else 0
            
            # Add to analytics
            self.analytics_data['views_per_hour'].append(self.view_count)
            self.analytics_data['success_rate_history'].append(success_rate)
            
            # Update analytics table
            if hasattr(self, 'analytics_table'):
                row = self.analytics_table.rowCount()
                self.analytics_table.insertRow(row)
                self.analytics_table.setItem(row, 0, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
                self.analytics_table.setItem(row, 1, QTableWidgetItem(str(self.view_count)))
                self.analytics_table.setItem(row, 2, QTableWidgetItem(f"{success_rate:.1f}%"))
                self.analytics_table.setItem(row, 3, QTableWidgetItem(f"{self.watch_time}s"))
                self.analytics_table.setItem(row, 4, QTableWidgetItem(str(self.error_count)))
                self.analytics_table.setItem(row, 5, QTableWidgetItem("🟢 Active" if self.running else "🔴 Stopped"))
                
                # Keep only last 100 rows
                if self.analytics_table.rowCount() > 100:
                    self.analytics_table.removeRow(0)
        except Exception as e:
            self.log(f"⚠️ Analytics update error: {e}")
    
    def update_stats(self, stats):
        """10X UPGRADE: Enhanced stats display"""
        stats_str = (
            f"📊 Performance Metrics\n"
            f"{'='*30}\n"
            f"Views Completed: {stats.get('views', self.view_count)}\n"
            f"Errors: {stats.get('errors', self.error_count)}\n"
            f"Status: {'🟢 Running' if self.running else '🔴 Stopped'}\n"
            f"Active Threads: {self.active_threads}\n"
            f"Queue Length: {len(self.multi_video_queue)}\n"
            f"Success Rate: {((self.view_count / (self.view_count + self.error_count)) * 100) if (self.view_count + self.error_count) > 0 else 0:.1f}%\n"
            f"Views Today: {self.total_views_today}\n"
            f"Session Time: {str(timedelta(seconds=int(time.time() - self.start_time)))}"
        )
        if hasattr(self, 'stats_text'):
            self.stats_text.setText(stats_str)

    ##########################
    # Tab 6: Settings
    def init_tab_settings(self):
        layout = QVBoxLayout()
        self.tab_settings.setLayout(layout)

        title = QLabel("⚙️ Settings")
        title.setFont(QFont("Consolas", 19, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Browser Settings
        browser_group = QGroupBox("🌐 Browser Settings")
        browser_layout = QVBoxLayout()

        # Cache Settings
        cache_layout = QHBoxLayout()
        self.clear_cache_checkbox = QCheckBox("Clear Cache Between Views")
        self.clear_cache_checkbox.setChecked(self.clear_cache)
        self.clear_cache_checkbox.stateChanged.connect(lambda s: setattr(self, "clear_cache", s == Qt.Checked))
        cache_layout.addWidget(self.clear_cache_checkbox)

        self.clear_cookies_checkbox = QCheckBox("Clear Cookies Between Views")
        self.clear_cookies_checkbox.setChecked(self.clear_cookies)
        self.clear_cookies_checkbox.stateChanged.connect(lambda s: setattr(self, "clear_cookies", s == Qt.Checked))
        cache_layout.addWidget(self.clear_cookies_checkbox)
        browser_layout.addLayout(cache_layout)

        # View Behavior
        behavior_layout = QHBoxLayout()
        self.random_watch_time_checkbox = QCheckBox("Randomize Watch Time")
        self.random_watch_time_checkbox.setChecked(self.random_watch_time)
        self.random_watch_time_checkbox.stateChanged.connect(lambda s: setattr(self, "random_watch_time", s == Qt.Checked))
        behavior_layout.addWidget(self.random_watch_time_checkbox)

        self.random_delay_checkbox = QCheckBox("Randomize View Delays")
        self.random_delay_checkbox.setChecked(self.random_delay)
        self.random_delay_checkbox.stateChanged.connect(lambda s: setattr(self, "random_delay", s == Qt.Checked))
        behavior_layout.addWidget(self.random_delay_checkbox)
        browser_layout.addLayout(behavior_layout)

        browser_group.setLayout(browser_layout)
        layout.addWidget(browser_group)

        # Advanced Features
        advanced_group = QGroupBox("🔬 Advanced Features")
        advanced_layout = QVBoxLayout()

        # Auto Actions
        auto_layout = QHBoxLayout()
        self.auto_like_checkbox = QCheckBox("Auto-Like Videos")
        self.auto_like_checkbox.setChecked(self.auto_like)
        self.auto_like_checkbox.stateChanged.connect(lambda s: setattr(self, "auto_like", s == Qt.Checked))
        auto_layout.addWidget(self.auto_like_checkbox)

        self.auto_subscribe_checkbox = QCheckBox("Auto-Subscribe")
        self.auto_subscribe_checkbox.setChecked(self.auto_subscribe)
        self.auto_subscribe_checkbox.stateChanged.connect(lambda s: setattr(self, "auto_subscribe", s == Qt.Checked))
        auto_layout.addWidget(self.auto_subscribe_checkbox)
        advanced_layout.addLayout(auto_layout)

        # View Behavior
        behavior_layout = QHBoxLayout()
        self.minimize_window_checkbox = QCheckBox("Minimize Window")
        self.minimize_window_checkbox.setChecked(self.minimize_window)
        self.minimize_window_checkbox.stateChanged.connect(lambda s: setattr(self, "minimize_window", s == Qt.Checked))
        behavior_layout.addWidget(self.minimize_window_checkbox)

        self.mute_audio_checkbox = QCheckBox("Mute Audio")
        self.mute_audio_checkbox.setChecked(self.mute_audio)
        self.mute_audio_checkbox.stateChanged.connect(lambda s: setattr(self, "mute_audio", s == Qt.Checked))
        behavior_layout.addWidget(self.mute_audio_checkbox)
        advanced_layout.addLayout(behavior_layout)

        # Auto-comment
        comment_layout = QHBoxLayout()
        self.auto_comment_checkbox = QCheckBox("Auto-Comment")
        self.auto_comment_checkbox.setChecked(self.auto_comment_enabled)
        self.auto_comment_checkbox.stateChanged.connect(lambda s: setattr(self, "auto_comment_enabled", s == Qt.Checked))
        comment_layout.addWidget(self.auto_comment_checkbox)
        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Comment text (optional)")
        self.comment_input.setText(self.comment_text)
        self.comment_input.textChanged.connect(lambda t: setattr(self, "comment_text", t))
        comment_layout.addWidget(self.comment_input)
        advanced_layout.addLayout(comment_layout)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        # Save Settings
        save_layout = QHBoxLayout()
        self.save_settings_btn = QPushButton("💾 Save Settings")
        self.save_settings_btn.clicked.connect(self.save_settings)
        save_layout.addWidget(self.save_settings_btn)

        self.load_settings_btn = QPushButton("📂 Load Settings")
        self.load_settings_btn.clicked.connect(self.load_settings)
        save_layout.addWidget(self.load_settings_btn)
        layout.addLayout(save_layout)

        # Help Text
        help_text = QLabel("""
        ⚠️ Important Notes:
        - Randomized settings help avoid detection
        - Clearing cache/cookies prevents tracking
        - Minimize window reduces CPU usage
        - Use proxies responsibly
        - 100X: Use mass start for multi-threaded viewing!
        """)
        help_text.setStyleSheet("""
            color: #666;
            font-size: 13px;
        """)
        layout.addWidget(help_text)

    def save_settings(self):
        settings = {
            "watch_time": self.watch_time,
            "view_delay": self.view_delay,
            "headless_mode": self.headless_mode,
            "incognito_mode": self.incognito_mode,
            "clear_cache": self.clear_cache,
            "clear_cookies": self.clear_cookies,
            "random_watch_time": self.random_watch_time,
            "random_delay": self.random_delay,
            "auto_like": self.auto_like,
            "auto_subscribe": self.auto_subscribe,
            "minimize_window": self.minimize_window,
            "mute_audio": self.mute_audio,
            "auto_comment_enabled": self.auto_comment_enabled,
            "comment_text": self.comment_text,
            "user_agents": self.user_agents
        }
        fname, _ = QFileDialog.getSaveFileName(self, "Save Settings", "", "JSON Files (*.json)")
        if fname:
            try:
                with open(fname, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=2)
                self.log(f"💾 Settings saved to {fname}")
            except Exception as e:
                self.log(f"❌ Failed to save settings: {e}")

    def load_settings(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Load Settings", "", "JSON Files (*.json)")
        if fname:
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                self.watch_time = settings.get("watch_time", self.watch_time)
                self.view_delay = settings.get("view_delay", self.view_delay)
                self.headless_mode = settings.get("headless_mode", self.headless_mode)
                self.incognito_mode = settings.get("incognito_mode", self.incognito_mode)
                self.clear_cache = settings.get("clear_cache", self.clear_cache)
                self.clear_cookies = settings.get("clear_cookies", self.clear_cookies)
                self.random_watch_time = settings.get("random_watch_time", self.random_watch_time)
                self.random_delay = settings.get("random_delay", self.random_delay)
                self.auto_like = settings.get("auto_like", self.auto_like)
                self.auto_subscribe = settings.get("auto_subscribe", self.auto_subscribe)
                self.minimize_window = settings.get("minimize_window", self.minimize_window)
                self.mute_audio = settings.get("mute_audio", self.mute_audio)
                self.auto_comment_enabled = settings.get("auto_comment_enabled", self.auto_comment_enabled)
                self.comment_text = settings.get("comment_text", self.comment_text)
                self.user_agents = settings.get("user_agents", self.user_agents)
                self.log(f"📂 Settings loaded from {fname}")
            except Exception as e:
                self.log(f"❌ Failed to load settings: {e}")

    ##########################
    # Tab 3: Analytics Dashboard (10X UPGRADE)
    def init_tab_stats(self):
        layout = QVBoxLayout()
        self.tab_stats.setLayout(layout)

        title = QLabel("📊 Advanced Analytics Dashboard")
        title.setFont(QFont("Consolas", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Stats Grid
        stats_grid = QHBoxLayout()
        
        # Real-time Stats Cards
        stats_card1 = QGroupBox("📈 Performance Metrics")
        stats_layout1 = QVBoxLayout()
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        self.stats_text.setStyleSheet("""
            background-color: #1a1a2e;
            color: #00ff00;
            font-family: Consolas;
            font-size: 14px;
            border: 1px solid #16213e;
        """)
        stats_layout1.addWidget(self.stats_text)
        stats_card1.setLayout(stats_layout1)
        stats_grid.addWidget(stats_card1)
        
        stats_card2 = QGroupBox("💻 System Resources")
        stats_layout2 = QVBoxLayout()
        self.system_stats_text = QTextEdit()
        self.system_stats_text.setReadOnly(True)
        self.system_stats_text.setMaximumHeight(200)
        self.system_stats_text.setStyleSheet("""
            background-color: #1a1a2e;
            color: #00d9ff;
            font-family: Consolas;
            font-size: 14px;
            border: 1px solid #16213e;
        """)
        stats_layout2.addWidget(self.system_stats_text)
        stats_card2.setLayout(stats_layout2)
        stats_grid.addWidget(stats_card2)
        
        layout.addLayout(stats_grid)
        
        # Analytics Table
        analytics_group = QGroupBox("📋 Detailed Analytics")
        analytics_layout = QVBoxLayout()
        self.analytics_table = QTableWidget()
        self.analytics_table.setColumnCount(6)
        self.analytics_table.setHorizontalHeaderLabels([
            "Time", "Views", "Success Rate", "Avg Watch Time", "Errors", "Status"
        ])
        self.analytics_table.horizontalHeader().setStretchLastSection(True)
        self.analytics_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                color: #00d9ff;
                gridline-color: #16213e;
            }
            QHeaderView::section {
                background-color: #0d1f3d;
                color: #00d9ff;
                padding: 8px;
                border: 1px solid #16213e;
                font-weight: bold;
            }
        """)
        analytics_layout.addWidget(self.analytics_table)
        analytics_group.setLayout(analytics_layout)
        layout.addWidget(analytics_group)
        
        # Export Analytics Button
        export_btn = QPushButton("💾 Export Analytics Data")
        export_btn.clicked.connect(self.export_analytics)
        layout.addWidget(export_btn)
        
        self.update_stats({})

    ##########################
    # Tab 4: Scheduler (10X UPGRADE - NEW)
    def init_tab_scheduler(self):
        layout = QVBoxLayout()
        self.tab_scheduler.setLayout(layout)

        title = QLabel("📅 Task Scheduler")
        title.setFont(QFont("Consolas", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Schedule Task Form
        schedule_group = QGroupBox("➕ Schedule New Task")
        schedule_layout = QVBoxLayout()
        
        # URL Input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("YouTube URL:"))
        self.schedule_url_input = QLineEdit()
        self.schedule_url_input.setPlaceholderText("Enter YouTube video URL")
        url_layout.addWidget(self.schedule_url_input)
        schedule_layout.addLayout(url_layout)
        
        # DateTime Picker
        datetime_layout = QHBoxLayout()
        datetime_layout.addWidget(QLabel("Schedule Time:"))
        self.schedule_datetime = QDateTimeEdit()
        self.schedule_datetime.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.schedule_datetime.setCalendarPopup(True)
        datetime_layout.addWidget(self.schedule_datetime)
        schedule_layout.addLayout(datetime_layout)
        
        # Recurring Options
        recurring_layout = QHBoxLayout()
        self.recurring_checkbox = QCheckBox("Recurring Task")
        recurring_layout.addWidget(self.recurring_checkbox)
        self.recurring_combo = QComboBox()
        self.recurring_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.recurring_combo.setEnabled(False)
        self.recurring_checkbox.stateChanged.connect(
            lambda s: self.recurring_combo.setEnabled(s == Qt.Checked)
        )
        recurring_layout.addWidget(self.recurring_combo)
        schedule_layout.addLayout(recurring_layout)
        
        # Add Schedule Button
        add_schedule_btn = QPushButton("➕ Add Scheduled Task")
        add_schedule_btn.clicked.connect(self.add_scheduled_task)
        schedule_layout.addWidget(add_schedule_btn)
        
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)
        
        # Scheduled Tasks List
        tasks_group = QGroupBox("📋 Scheduled Tasks")
        tasks_layout = QVBoxLayout()
        self.scheduled_tasks_list = QTableWidget()
        self.scheduled_tasks_list.setColumnCount(5)
        self.scheduled_tasks_list.setHorizontalHeaderLabels([
            "URL", "Scheduled Time", "Recurring", "Status", "Actions"
        ])
        self.scheduled_tasks_list.horizontalHeader().setStretchLastSection(True)
        tasks_layout.addWidget(self.scheduled_tasks_list)
        
        # Task Controls
        task_controls = QHBoxLayout()
        remove_task_btn = QPushButton("🗑️ Remove Selected")
        remove_task_btn.clicked.connect(self.remove_scheduled_task)
        task_controls.addWidget(remove_task_btn)
        toggle_scheduler_btn = QPushButton("▶️ Start Scheduler")
        toggle_scheduler_btn.clicked.connect(self.toggle_scheduler)
        task_controls.addWidget(toggle_scheduler_btn)
        tasks_layout.addLayout(task_controls)
        
        tasks_group.setLayout(tasks_layout)
        layout.addWidget(tasks_group)

    ##########################
    # Tab 5: Video Tools (10X UPGRADE - NEW)
    def init_tab_video_tools(self):
        layout = QVBoxLayout()
        self.tab_video_tools.setLayout(layout)

        title = QLabel("🎥 Video Analytics & Tools")
        title.setFont(QFont("Consolas", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Video URL Input
        url_group = QGroupBox("🔍 Video Analysis")
        url_layout = QVBoxLayout()
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("YouTube URL:"))
        self.video_analysis_url = QLineEdit()
        self.video_analysis_url.setPlaceholderText("Enter YouTube video URL to analyze")
        input_layout.addWidget(self.video_analysis_url)
        analyze_btn = QPushButton("🔍 Analyze Video")
        analyze_btn.clicked.connect(self.analyze_video)
        input_layout.addWidget(analyze_btn)
        url_layout.addLayout(input_layout)
        
        # Video Info Display
        self.video_info_display = QTextEdit()
        self.video_info_display.setReadOnly(True)
        self.video_info_display.setMaximumHeight(200)
        self.video_info_display.setStyleSheet("""
            background-color: #1a1a2e;
            color: #00d9ff;
            font-family: Consolas;
            font-size: 13px;
        """)
        url_layout.addWidget(self.video_info_display)
        
        # Video Tools Buttons
        tools_layout = QHBoxLayout()
        download_thumb_btn = QPushButton("🖼️ Download Thumbnail")
        download_thumb_btn.clicked.connect(self.download_video_thumbnail_ui)
        tools_layout.addWidget(download_thumb_btn)
        
        export_info_btn = QPushButton("💾 Export Video Info")
        export_info_btn.clicked.connect(self.export_video_info)
        tools_layout.addWidget(export_info_btn)
        
        url_layout.addLayout(tools_layout)
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)
        
        # Video Analytics History
        history_group = QGroupBox("📊 Analyzed Videos")
        history_layout = QVBoxLayout()
        self.video_history_table = QTableWidget()
        self.video_history_table.setColumnCount(5)
        self.video_history_table.setHorizontalHeaderLabels([
            "Title", "Views", "Likes", "Duration", "Analyzed"
        ])
        history_layout.addWidget(self.video_history_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

    ##########################
    # Tab 6: AI Assistant (10X UPGRADE)
    def init_tab_ai_tools(self):
        layout = QVBoxLayout()
        self.tab_ai.setLayout(layout)

        title = QLabel("🧠 AI Assistant & Smart Features")
        title.setFont(QFont("Consolas", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # AI Comment Generator
        comment_group = QGroupBox("💬 AI Comment Generator")
        comment_layout = QVBoxLayout()
        
        comment_info = QLabel("Generate natural, engaging comments for videos:")
        comment_layout.addWidget(comment_info)
        
        self.ai_comment_output = QTextEdit()
        self.ai_comment_output.setReadOnly(True)
        self.ai_comment_output.setMaximumHeight(100)
        self.ai_comment_output.setPlaceholderText("Generated comment will appear here...")
        comment_layout.addWidget(self.ai_comment_output)
        
        comment_controls = QHBoxLayout()
        generate_comment_btn = QPushButton("✨ Generate Comment")
        generate_comment_btn.clicked.connect(self.generate_ai_comment)
        comment_controls.addWidget(generate_comment_btn)
        
        use_comment_btn = QPushButton("✅ Use This Comment")
        use_comment_btn.clicked.connect(self.use_generated_comment)
        comment_controls.addWidget(use_comment_btn)
        comment_layout.addLayout(comment_controls)
        
        comment_group.setLayout(comment_layout)
        layout.addWidget(comment_group)
        
        # Smart Delay Calculator
        delay_group = QGroupBox("⏱️ Smart Delay Calculator")
        delay_layout = QVBoxLayout()
        
        delay_info = QLabel("AI calculates optimal delays based on your activity patterns:")
        delay_layout.addWidget(delay_info)
        
        self.smart_delay_display = QLabel("Recommended Delay: -- seconds")
        self.smart_delay_display.setStyleSheet("font-size: 16px; color: #00ffff; font-weight: bold;")
        delay_layout.addWidget(self.smart_delay_display)
        
        calculate_delay_btn = QPushButton("🧮 Calculate Optimal Delay")
        calculate_delay_btn.clicked.connect(self.calculate_smart_delay)
        delay_layout.addWidget(calculate_delay_btn)
        
        delay_group.setLayout(delay_layout)
        layout.addWidget(delay_group)
        
        # AI Suggestions
        suggestions_group = QGroupBox("💡 AI Suggestions")
        suggestions_layout = QVBoxLayout()
        self.ai_suggestions_text = QTextEdit()
        self.ai_suggestions_text.setReadOnly(True)
        self.ai_suggestions_text.setPlaceholderText("AI suggestions will appear here based on your usage patterns...")
        suggestions_layout.addWidget(self.ai_suggestions_text)
        
        refresh_suggestions_btn = QPushButton("🔄 Refresh Suggestions")
        refresh_suggestions_btn.clicked.connect(self.generate_ai_suggestions)
        suggestions_layout.addWidget(refresh_suggestions_btn)
        
        suggestions_group.setLayout(suggestions_layout)
        layout.addWidget(suggestions_group)

    ##########################
    # Tab 7: Help
    def init_tab_help(self):
        layout = QVBoxLayout()
        self.tab_help.setLayout(layout)

        title = QLabel("❓ Help & Info")
        title.setFont(QFont("Consolas", 19, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setStyleSheet("""
            background-color: #111;
            color: #00ffe7;
            font-family: Consolas;
            font-size: 14px;
        """)
        help_text.setText(
            f"{APP_NAME} {APP_VERSION} - 10X UPGRADE\n\n"
            "🚀 NEW FEATURES IN v4.0.0:\n"
            "• 📅 Task Scheduler - Schedule views for specific times\n"
            "• 📊 Advanced Analytics Dashboard - Real-time performance tracking\n"
            "• 🎥 Video Analytics & Tools - Deep video analysis\n"
            "• 🧠 AI Assistant - Smart comment generation & suggestions\n"
            "• ⏱️ Smart Delay Calculator - AI-optimized timing\n"
            "• 📈 Enhanced Statistics - Detailed metrics & export\n\n"
            "✨ CORE FEATURES:\n"
            "• Multi-video queue & mass start (up to 200 threads)\n"
            "• User-Agent Spoofing & Rotation\n"
            "• Proxy Pool & Automatic Rotation\n"
            "• Adjustable watch time & smart delays\n"
            "• Headless Chrome with undetected mode\n"
            "• Auto-Like, Auto-Subscribe, Auto-Comment\n"
            "• Video info scraping & thumbnail download\n"
            "• Live stream detection\n"
            "• Export logs/history/settings/analytics\n"
            "• Real-time system resource monitoring\n"
            "• Queue management (up to 500 videos)\n"
            "• URL history tracking (up to 100 entries)\n\n"
            "💡 TIPS:\n"
            "• Use the Scheduler for automated campaigns\n"
            "• Check Analytics tab for performance insights\n"
            "• Use AI Assistant for optimal settings\n"
            "• Export analytics for detailed reporting\n"
            "• Video Tools help analyze competitor content\n\n"
            "⚠️ IMPORTANT:\n"
            "• Auto-commenting requires Google login\n"
            "• Use proxies responsibly\n"
            "• Respect YouTube's Terms of Service\n"
            "• For educational purposes only\n\n"
            "Developed by PlayNexus // © 2025 Nortaq\n"
            "GitHub: https://github.com/PlayNexusHub/Galaxy-YouTube-ViewBot-Pro-PlayNexus"
        )
        layout.addWidget(help_text)

    ##########################
    # Feature implementations below:

    def scrape_video_info(self, driver):
        info = {}
        try:
            title = driver.title
            info["title"] = title.replace(" - YouTube", "").strip()
            try:
                views_elem = driver.find_element("xpath", '//*[@id="count"]/yt-view-count-renderer/span[1]')
                views_text = views_elem.text if views_elem else "N/A"
            except Exception:
                views_text = "N/A"
            info["views"] = views_text
            # Likes selector (new YouTube changes often, fallback used)
            try:
                like_elem = driver.find_element("xpath", '//ytd-toggle-button-renderer[1]//yt-formatted-string[@id="text"]')
                likes = like_elem.get_attribute('aria-label') or like_elem.text
                info["likes"] = likes
            except:
                info["likes"] = "N/A"
        except Exception as e:
            self.signals.log.emit(f"⚠️ Video info scrape failed: {e}")
        return info

    def detect_live_stream(self, driver):
        try:
            live_badge = driver.find_elements("xpath", '//span[contains(text(),"LIVE")]')
            return bool(live_badge)
        except:
            return False

    def get_video_duration(self, driver):
        try:
            # Try multiple selectors for video duration
            selectors = [
                '//*[@class="ytp-time-duration"]',
                '//span[@class="ytp-time-duration"]',
                '//div[@class="ytp-time-duration"]'
            ]
            for selector in selectors:
                try:
                    dur_elem = driver.find_element("xpath", selector)
                    if dur_elem:
                        return dur_elem.text
                except:
                    continue
            return "N/A"
        except:
            return "N/A"

    def auto_click_like(self, driver):
        try:
            like_btn = driver.find_element("xpath", '//ytd-toggle-button-renderer[1]//a[@aria-pressed]')
            like_btn.click()
            self.signals.log.emit("👍 Auto-Liked video.")
        except Exception:
            self.signals.log.emit("⚠️ Auto-Like failed (probably not logged in).")

    def auto_subscribe_channel(self, driver):
        try:
            sub_btn = driver.find_element("xpath", '//tp-yt-paper-button[@aria-label and contains(@aria-label,"Subscribe")]')
            if sub_btn.text.lower() == "subscribe":
                sub_btn.click()
                self.signals.log.emit("➕ Auto-Subscribed to channel.")
            else:
                self.signals.log.emit("ℹ️ Already subscribed or subscribe button not found.")
        except Exception:
            self.signals.log.emit("⚠️ Auto-Subscribe failed (probably not logged in).")

    def auto_comment(self, driver, comment_text=None):
        # 100X: Try to post a comment if logged in and allowed
        if not comment_text:
            comment_text = self.comment_text
        try:
            # Scroll to comment box
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            comment_box = driver.find_element("xpath", '//ytd-comment-simplebox-renderer')
            comment_box.click()
            time.sleep(1)
            input_box = driver.find_element("xpath", '//div[@id="contenteditable-root"]')
            input_box.send_keys(comment_text)
            time.sleep(1)
            submit_btn = driver.find_element("xpath", '//ytd-button-renderer[@id="submit-button"]//a')
            submit_btn.click()
            self.signals.log.emit(f"💬 Auto-Commented: {comment_text}")
        except Exception:
            self.signals.log.emit("⚠️ Auto-Comment failed (probably not logged in or not allowed).")

    ##########################
    # Additional helpers for multi-video queue, thumbnail download, recent comments fetching

    def download_video_thumbnail(self, url):
        try:
            video_id = self.extract_video_id(url)
            thumb_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            fname = f"{video_id}_thumbnail.jpg"
            urllib.request.urlretrieve(thumb_url, fname)
            self.log(f"✅ Thumbnail downloaded: {fname}")
        except Exception as e:
            self.log(f"❌ Failed to download thumbnail: {e}")

    def extract_video_id(self, url):
        # Simple extractor for youtube video id
        import re
        m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
        return m.group(1) if m else None

    def fetch_recent_comments(self, driver):
        # 10X UPGRADE: Enhanced comment fetching
        self.log("💬 Fetching recent comments is not fully implemented.")
    
    ##########################
    # 10X UPGRADE: New Feature Implementations
    
    def add_scheduled_task(self):
        """Add a new scheduled task"""
        url = self.schedule_url_input.text().strip()
        if not url.startswith("http"):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid YouTube URL")
            return
        
        scheduled_time = self.schedule_datetime.dateTime().toPyDateTime()
        is_recurring = self.recurring_checkbox.isChecked()
        recurring_type = self.recurring_combo.currentText() if is_recurring else None
        
        task = {
            'url': url,
            'scheduled_time': scheduled_time,
            'recurring': is_recurring,
            'recurring_type': recurring_type,
            'status': 'Pending',
            'id': len(self.scheduled_tasks) + 1
        }
        
        self.scheduled_tasks.append(task)
        self.update_scheduled_tasks_table()
        self.schedule_url_input.clear()
        self.log(f"✅ Scheduled task added for {scheduled_time.strftime('%Y-%m-%d %H:%M')}")
    
    def update_scheduled_tasks_table(self):
        """Update the scheduled tasks table"""
        if not hasattr(self, 'scheduled_tasks_list'):
            return
        
        self.scheduled_tasks_list.setRowCount(len(self.scheduled_tasks))
        for i, task in enumerate(self.scheduled_tasks):
            self.scheduled_tasks_list.setItem(i, 0, QTableWidgetItem(task['url'][:50] + "..."))
            self.scheduled_tasks_list.setItem(i, 1, QTableWidgetItem(task['scheduled_time'].strftime('%Y-%m-%d %H:%M')))
            self.scheduled_tasks_list.setItem(i, 2, QTableWidgetItem(task['recurring_type'] or "One-time"))
            self.scheduled_tasks_list.setItem(i, 3, QTableWidgetItem(task['status']))
            self.scheduled_tasks_list.setItem(i, 4, QTableWidgetItem("⏸️ Pause" if task['status'] == 'Active' else "▶️ Activate"))
    
    def remove_scheduled_task(self):
        """Remove selected scheduled task"""
        row = self.scheduled_tasks_list.currentRow()
        if row >= 0 and row < len(self.scheduled_tasks):
            task = self.scheduled_tasks.pop(row)
            self.update_scheduled_tasks_table()
            self.log(f"🗑️ Removed scheduled task: {task['url'][:50]}")
    
    def toggle_scheduler(self):
        """Toggle scheduler on/off"""
        self.scheduler_running = not self.scheduler_running
        self.log(f"{'▶️ Started' if self.scheduler_running else '⏸️ Stopped'} scheduler")
    
    def check_scheduled_tasks(self):
        """Check and execute scheduled tasks"""
        if not self.scheduler_running:
            return
        
        now = datetime.now()
        for task in self.scheduled_tasks:
            if task['status'] == 'Pending' and now >= task['scheduled_time']:
                self.execute_scheduled_task(task)
    
    def execute_scheduled_task(self, task):
        """Execute a scheduled task"""
        task['status'] = 'Executing'
        self.log(f"⏰ Executing scheduled task: {task['url']}")
        
        # Add to queue and start
        if task['url'] not in self.multi_video_queue:
            self.multi_video_queue.append(task['url'])
            if hasattr(self, 'queue_list'):
                self.queue_list.addItem(task['url'])
        
        if not self.running:
            self.url_input.setText(task['url'])
            self.start_bot()
        
        # Handle recurring tasks
        if task['recurring']:
            if task['recurring_type'] == 'Daily':
                task['scheduled_time'] = task['scheduled_time'] + timedelta(days=1)
            elif task['recurring_type'] == 'Weekly':
                task['scheduled_time'] = task['scheduled_time'] + timedelta(weeks=1)
            elif task['recurring_type'] == 'Monthly':
                task['scheduled_time'] = task['scheduled_time'] + timedelta(days=30)
            task['status'] = 'Pending'
        else:
            task['status'] = 'Completed'
        
        self.update_scheduled_tasks_table()
    
    def handle_scheduled_task(self, url):
        """Handle scheduled task trigger"""
        self.log(f"📅 Scheduled task triggered: {url}")
    
    def analyze_video(self):
        """10X UPGRADE: Analyze video information"""
        url = self.video_analysis_url.text().strip()
        if not url.startswith("http"):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid YouTube URL")
            return
        
        self.log(f"🔍 Analyzing video: {url}")
        self.video_info_display.setText("Analyzing video... Please wait...")
        
        # Run analysis in thread
        threading.Thread(target=self._analyze_video_thread, args=(url,), daemon=True).start()
    
    def _analyze_video_thread(self, url):
        """Analyze video in background thread"""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            
            driver = uc.Chrome(options=options)
            driver.get(url)
            time.sleep(3)
            
            info = self.scrape_video_info(driver)
            info['url'] = url
            info['analyzed_at'] = datetime.now().isoformat()
            
            # Update display
            info_text = f"""📹 Video Analysis Results
{'='*40}
Title: {info.get('title', 'N/A')}
Views: {info.get('views', 'N/A')}
Likes: {info.get('likes', 'N/A')}
Duration: {info.get('duration', 'N/A')}
Live Stream: {'Yes' if self.detect_live_stream(driver) else 'No'}
Video ID: {self.extract_video_id(url) or 'N/A'}
Analyzed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self.video_info_display.setText(info_text)
            
            # Add to history
            if hasattr(self, 'video_history_table'):
                row = self.video_history_table.rowCount()
                self.video_history_table.insertRow(row)
                self.video_history_table.setItem(row, 0, QTableWidgetItem(info.get('title', 'N/A')[:30]))
                self.video_history_table.setItem(row, 1, QTableWidgetItem(str(info.get('views', 'N/A'))))
                self.video_history_table.setItem(row, 2, QTableWidgetItem(str(info.get('likes', 'N/A'))))
                self.video_history_table.setItem(row, 3, QTableWidgetItem(str(info.get('duration', 'N/A'))))
                self.video_history_table.setItem(row, 4, QTableWidgetItem(datetime.now().strftime('%Y-%m-%d %H:%M')))
            
            # Cache video info
            self.video_cache[url] = info
            self.analytics_data['video_analytics'].append(info)
            
            driver.quit()
            self.log("✅ Video analysis completed")
        except Exception as e:
            self.video_info_display.setText(f"❌ Error analyzing video: {str(e)}")
            self.log(f"❌ Analysis error: {e}")
    
    def download_video_thumbnail_ui(self):
        """Download thumbnail from UI"""
        url = self.video_analysis_url.text().strip() or self.url_input.text().strip()
        if url:
            self.download_video_thumbnail(url)
        else:
            QMessageBox.warning(self, "No URL", "Please enter a YouTube URL first")
    
    def export_video_info(self):
        """Export video information"""
        url = self.video_analysis_url.text().strip()
        if url not in self.video_cache:
            QMessageBox.warning(self, "No Data", "Please analyze the video first")
            return
        
        fname, _ = QFileDialog.getSaveFileName(self, "Export Video Info", "", "JSON Files (*.json)")
        if fname:
            try:
                with open(fname, 'w', encoding='utf-8') as f:
                    json.dump(self.video_cache[url], f, indent=2)
                self.log(f"💾 Video info exported to {fname}")
            except Exception as e:
                self.log(f"❌ Export error: {e}")
    
    def generate_ai_comment(self):
        """10X UPGRADE: Generate AI comment"""
        comment = random.choice(self.comment_templates)
        # Add some variation
        variations = ["", "!", "!!", " 🚀", " 💯", " ⭐"]
        comment += random.choice(variations)
        self.ai_comment_output.setText(comment)
        self.log("✨ Generated AI comment")
    
    def use_generated_comment(self):
        """Use the generated comment"""
        comment = self.ai_comment_output.toPlainText()
        if comment:
            self.comment_text = comment
            if hasattr(self, 'comment_input'):
                self.comment_input.setText(comment)
            self.log(f"✅ Using comment: {comment[:50]}...")
    
    def calculate_smart_delay(self):
        """10X UPGRADE: Calculate optimal delay using AI"""
        # Analyze recent activity patterns
        if len(self.analytics_data['success_rate_history']) < 5:
            recommended = self.view_delay
        else:
            # Calculate based on success rate
            avg_success = sum(self.analytics_data['success_rate_history'][-10:]) / min(10, len(self.analytics_data['success_rate_history']))
            if avg_success < 80:
                recommended = min(self.view_delay * 1.5, 60)  # Increase delay if low success
            elif avg_success > 95:
                recommended = max(self.view_delay * 0.8, 1)  # Decrease if very successful
            else:
                recommended = self.view_delay
        
        self.smart_delay_display.setText(f"Recommended Delay: {recommended:.1f} seconds")
        self.view_delay = int(recommended)
        if hasattr(self, 'view_delay_spin'):
            self.view_delay_spin.setValue(int(recommended))
        self.log(f"🧮 Calculated optimal delay: {recommended:.1f} seconds")
    
    def generate_ai_suggestions(self):
        """Generate AI suggestions based on usage"""
        suggestions = []
        
        if self.error_count > self.view_count * 0.2:
            suggestions.append("⚠️ High error rate detected. Consider increasing delays or using proxies.")
        
        if self.cpu_usage > 80:
            suggestions.append("💻 High CPU usage. Reduce concurrent views to improve stability.")
        
        if len(self.multi_video_queue) > 50:
            suggestions.append("📋 Large queue detected. Consider processing in batches.")
        
        if not self.rotate_proxies and self.view_count > 100:
            suggestions.append("🔒 Consider enabling proxy rotation for better results.")
        
        if self.view_delay < 2:
            suggestions.append("⏱️ Very short delays may trigger rate limiting. Consider increasing delay.")
        
        if not suggestions:
            suggestions.append("✅ Everything looks good! Your settings are optimal.")
        
        self.ai_suggestions_text.setText("\n".join([f"• {s}" for s in suggestions]))
        self.log("💡 Generated AI suggestions")
    
    def export_analytics(self):
        """Export analytics data"""
        fname, _ = QFileDialog.getSaveFileName(self, "Export Analytics", "", "CSV Files (*.csv);;JSON Files (*.json)")
        if fname:
            try:
                if fname.endswith('.csv'):
                    with open(fname, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Time', 'Views', 'Errors', 'Success Rate', 'CPU', 'RAM'])
                        for i in range(min(100, len(self.analytics_data['success_rate_history']))):
                            writer.writerow([
                                datetime.now().strftime('%H:%M:%S'),
                                self.view_count,
                                self.error_count,
                                self.analytics_data['success_rate_history'][i] if i < len(self.analytics_data['success_rate_history']) else 0,
                                self.cpu_usage,
                                self.ram_usage
                            ])
                else:
                    with open(fname, 'w', encoding='utf-8') as f:
                        json.dump(self.analytics_data, f, indent=2, default=str)
                self.log(f"💾 Analytics exported to {fname}")
            except Exception as e:
                self.log(f"❌ Export error: {e}")
    
    def update_video_analytics(self, data):
        """Update video analytics display"""
        if hasattr(self, 'video_history_table') and data:
            row = self.video_history_table.rowCount()
            self.video_history_table.insertRow(row)
            self.video_history_table.setItem(row, 0, QTableWidgetItem(str(data.get('title', 'N/A')[:30])))
            self.video_history_table.setItem(row, 1, QTableWidgetItem(str(data.get('views', 'N/A'))))
            self.video_history_table.setItem(row, 2, QTableWidgetItem(str(data.get('likes', 'N/A'))))
            self.video_history_table.setItem(row, 3, QTableWidgetItem(str(data.get('duration', 'N/A'))))
            self.video_history_table.setItem(row, 4, QTableWidgetItem(datetime.now().strftime('%Y-%m-%d %H:%M')))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = YouTubeViewBot()
    win.show()
    sys.exit(app.exec_())
