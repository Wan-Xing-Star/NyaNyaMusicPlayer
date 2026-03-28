import sqlite3
import uuid

# 插入一个唯一标识符
test_id = str(uuid.uuid4())

conn = sqlite3.connect('Z:\\Project\\NyaNyaMusicPlayer\\data\\main.db')
cursor = conn.cursor()

# 确保表存在
cursor.execute("""
CREATE TABLE IF NOT EXISTS test_table (
    SongID INTEGER PRIMARY KEY AUTOINCREMENT,INSERT INTO songs (SongName, Duration, Artists, PlayCount, LoopCount, FirstPlay, LastPlay) VALUES ("hello", 213, "Gura;", 0, 0, 12, 123);
COMMITINSERT INTO songs (SongName, Duration, Artists, PlayCount, LoopCount, FirstPlay, LastPlay) VALUES ("hello", 213, "Gura;", 0, 0, 12, 123)
COMMITINSERT INTO songs (SongName, Duration, Artists, PlayCount, LoopCount, FirstPlay, LastPlay) VALUES ("hello", 213, "Gura;", 0, 0, 12, 123)INSERT INTO songs (SongName, Duration, Artists, PlayCount, LoopCount, FirstPlay, LastPlay) VALUES ("hello", 213, "Gura", 0, 0, 12, 123)
    SongName TEXT UNIQUE,
    TestMarker TEXT
)
""")

# 插入测试数据
try:
    cursor.execute("INSERT INTO test_table (SongName, TestMarker) VALUES (?, ?)", 
                   ("test_marker", test_id))
    conn.commit()
    print(f"测试标记已插入: {test_id}")
    print("请在你的数据库插件中查询 test_table 表，看是否有这条记录")
    print("查询: SELECT * FROM test_table WHERE TestMarker = '{}'".format(test_id))
except sqlite3.IntegrityError:
    print("测试标记已存在，先删除")
    cursor.execute("DELETE FROM test_table WHERE SongName = 'test_marker'")
    conn.commit()

conn.close()