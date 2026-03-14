import sys
import os
import json
import ctypes
#PySide6 - 6.10.2
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,QMessageBox,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

# ---------- 设置 Windows 任务栏图标所需（必须在 QApplication 创建前执行）----------
try:
    myappid = 'mycompany.songviewer.version1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except AttributeError:
    pass

# ---------- 资源路径辅助函数（兼容开发环境和打包后的 exe）----------
def resource_path(relative_path):
    path = os.path.normpath(os.path.join(os.getcwd(), relative_path))
    return path

# ---------- 示例数据 ----------
SAMPLE_DATA = {
    "all": 0,
    "year": {"2026": 0},
    "month": {"202603": 0},
    "each_song": {}
}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("歌曲数据展示")
        self.resize(900, 700)

        icon_path = resource_path("ico/main.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.path = resource_path("data/main.json")
        self.data = self.load_data()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 总播放时长
        total_seconds = self.data.get('all', 0)
        total_hours = total_seconds // 3600
        total_label = QLabel(f"总播放时长: {total_hours} 小时")
        total_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        total_label.setFont(font)
        total_label.setStyleSheet("color: #5dade2; margin: 10px;")
        main_layout.addWidget(total_label)

        # 年份和月份表格
        tables_layout = QHBoxLayout()

        self.year_table = QTableWidget()
        self.year_table.setColumnCount(2)
        self.year_table.setHorizontalHeaderLabels(["年份", "播放小时"])
        self.year_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.year_table.setMaximumHeight(150)
        self.populate_year_table()
        tables_layout.addWidget(self.year_table)

        self.month_table = QTableWidget()
        self.month_table.setColumnCount(2)
        self.month_table.setHorizontalHeaderLabels(["月份", "播放小时"])
        self.month_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.month_table.setMaximumHeight(150)
        self.populate_month_table()
        tables_layout.addWidget(self.month_table)

        main_layout.addLayout(tables_layout)

        # 详细信息按钮
        self.detail_button = QPushButton("显示歌曲列表")
        self.detail_button.clicked.connect(self.toggle_song_table)
        main_layout.addWidget(self.detail_button, alignment=Qt.AlignCenter)

        # 歌曲表格（初始隐藏）
        self.song_table = QTableWidget()
        self.song_table.setColumnCount(4)
        self.song_table.setHorizontalHeaderLabels(["歌曲名", "播放次数", "时长", "艺术家"])
        self.song_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.song_table.setSortingEnabled(True)          # 启用排序
        self.populate_song_table()
        self.song_table.setVisible(False)
        main_layout.addWidget(self.song_table)

    def load_data(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "each_song" in data:
                    return data
                else:
                    self.warn()
                    return SAMPLE_DATA
        except FileNotFoundError:
            self.warn()
            return SAMPLE_DATA
        except json.JSONDecodeError:
            self.warn()
            return SAMPLE_DATA

    def warn(self):
        QMessageBox.warning(self,"Error","数据文件丢失/严重损坏\n无法展示")
        sys.exit(0)
        

    def populate_year_table(self):
        year_data = self.data.get('year', {})
        self.year_table.setRowCount(len(year_data))
        for row, (year, seconds) in enumerate(year_data.items()):
            hours = seconds // 3600
            year_item = QTableWidgetItem(str(year))
            year_item.setFlags(year_item.flags() & ~Qt.ItemIsEditable)
            hour_item = QTableWidgetItem(str(hours))
            hour_item.setFlags(hour_item.flags() & ~Qt.ItemIsEditable)
            self.year_table.setItem(row, 0, year_item)
            self.year_table.setItem(row, 1, hour_item)

    def populate_month_table(self):
        month_data = self.data.get('month', {})
        self.month_table.setRowCount(len(month_data))
        for row, (month, seconds) in enumerate(month_data.items()):
            hours = seconds // 3600
            month_item = QTableWidgetItem(str(month))
            month_item.setFlags(month_item.flags() & ~Qt.ItemIsEditable)
            hour_item = QTableWidgetItem(str(hours))
            hour_item.setFlags(hour_item.flags() & ~Qt.ItemIsEditable)
            self.month_table.setItem(row, 0, month_item)
            self.month_table.setItem(row, 1, hour_item)

    def populate_song_table(self):
        """填充歌曲表格，并确保播放次数列按数值排序"""
        # 自定义数值项，用于播放次数列的正确排序
        class NumericTableWidgetItem(QTableWidgetItem):
            def __lt__(self, other):
                if isinstance(other, QTableWidgetItem):
                    self_val = self.data(Qt.UserRole)
                    other_val = other.data(Qt.UserRole)
                    if self_val is not None and other_val is not None:
                        try:
                            return float(self_val) < float(other_val)
                        except (ValueError, TypeError):
                            pass
                return super().__lt__(other)

        each_song = self.data.get("each_song", {})
        self.song_table.setRowCount(len(each_song))

        for row, (song_name, info) in enumerate(each_song.items()):
            play_count = info[0] if len(info) > 0 else 0
            duration = info[1][0] if len(info) > 1 and isinstance(info[1], list) and len(info[1]) > 0 else "未知"
            artists = info[1][1] if len(info) > 1 and isinstance(info[1], list) and len(info[1]) > 1 else []
            artist_str = ", ".join(artists) if artists else "未知"

            song_item = QTableWidgetItem(song_name)
            song_item.setData(Qt.UserRole, song_name)

            # 播放次数使用自定义数值项
            count_item = NumericTableWidgetItem(str(play_count))
            count_item.setData(Qt.UserRole, play_count)
            count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)  # 右对齐

            duration_item = QTableWidgetItem(duration)
            artist_item = QTableWidgetItem(artist_str)

            for item in (song_item, count_item, duration_item, artist_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.song_table.setItem(row, 0, song_item)
            self.song_table.setItem(row, 1, count_item)
            self.song_table.setItem(row, 2, duration_item)
            self.song_table.setItem(row, 3, artist_item)

        # 调整列宽
        self.song_table.setColumnWidth(1, 100)
        self.song_table.setColumnWidth(2, 80)
        self.song_table.setColumnWidth(3, 150)

    def toggle_song_table(self):
        if self.song_table.isVisible():
            self.song_table.setVisible(False)
            self.detail_button.setText("显示歌曲列表")
        else:
            self.song_table.setVisible(True)
            self.detail_button.setText("隐藏歌曲列表")

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app_icon_path = resource_path("ico/main.ico")
    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())