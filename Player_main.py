#Python:3.13
import os,sys,json,random,time,atexit,threading,sqlite3
from typing import Any
import pygame # pip install pygame #2.6.1
from pynput import keyboard # pip install pynput #1.8.1
from mutagen._file import File # pip install mutagen

pygame.mixer.init() #初始化音乐播放器

is_pause = False
is_loop = False
running = True
main_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
music_play_list = []
Lock = threading.Lock()
message = None
running_environment = getattr(sys, 'frozen', False) # False 为python运行

class DataManage:
    def __init__(self,cfg: dict) -> None:
        log.write("初始化数据统计模块")
        self.path = os.path.normpath(os.path.join(main_path,"data/"))
        if not os.path.exists(self.path):
            os.makedirs(self.path,exist_ok=True)
            log.write("数据文件夹不存在,已创建",2)

        self.times = 0
        self.start_time = 0
        self.is_useful = False #判断时间的有效性
        self.is_ok = True # 判断是否记录数据
        self.today = time.strftime("%Y%m%d")
        self.encode = "utf-8"
        self.all_song = 0
        self.all_song_play_count = 0
        self.is_balance = cfg["平衡播放"]
        self.is_loop_balance = cfg["循环播放不计入平衡播放"]
        self.balance_limit = cfg["平衡播放限度"]
        self.main_data= {
            "all":0,
            "year":{},
            "month":{},
            }
        self.day_data = {
            "all":0,
            "song":{}
            }
        try:
            log.write("正在连接数据库",3)
            self.db = sqlite3.connect("./data/main.db")
        except Exception as e:
            log.write(f"在连接数据库时发生未知错误[{e}],统计功能将禁用",1)
            self.is_ok = False
        if self.is_ok:
            self.cursor = self.db.cursor()
            self.cursor.execute(    #初始化与创建表
            '''
            CREATE TABLE IF NOT EXISTS songs (
                SongName TEXT PRIMARY KEY,
                Duration INTEGER NOT NULL,
                Artists TEXT,
                PlayCount INTEGER,
                LoopCount INTEGER,
                FirstPlay INTEGER,
                LastPlay INTEGER
            )
            '''
            )
            self.db.commit()
            log.write("数据库连接成功",3)

        self.read()

    def path_to_name(self,song_path: str) ->str:
        return os.path.splitext(os.path.split(song_path)[1])[0]

    def set_n(self,n: int) -> None:
        """设置歌曲总数"""
        if not self.is_ok:
            return None
        self.all_song = n
        log.write(f"设置歌曲总数为[{n}]",3)

    def add_num(self,song_path: str) -> None:
        """为新歌曲添加数据"""
        if not self.is_ok:
            return None
        song_name = self.path_to_name(song_path)
        song_info = self.get_song(song_name)
        self.all_song_play_count += 0 if not song_info else song_info["PlayCount"]
        log.write(f"为歌曲[{song_name}]添加数据",3)
        if self.is_loop_balance:
            self.all_song_play_count -= 0 if not song_info else song_info["LoopCount"]
    
    def balance_play(self,song_path: str) -> bool:
        """判断歌曲是否可以播放（未触发平衡播放保护）"""   
        if not self.is_ok:
            return True
        song_name = self.path_to_name(song_path)
        if self.all_song == 0:
            log.write("歌曲总数为0,无法执行平衡播放保护",2)
            return True
        song_info = self.get_song(song_name)
        if song_info is None:
            log.write(f"歌曲[{song_name}]数据未找到,无法执行平衡播放保护",2)
            self.add_song(song_path)
            return True
        
        if song_info["PlayCount"] == 0:
            log.write(f"歌曲[{song_name}]第一次播放",3)
            return True
        
        play_count = song_info["PlayCount"] - (song_info["LoopCount"] if self.is_loop_balance else 0)
        play_count = max(0,play_count)
        average_play = self.all_song_play_count / self.all_song
        
        log.write(f"当前歌曲总数为[{self.all_song}],总播放次数为[{self.all_song_play_count}],平均播放次数为[{average_play}],[{song_name}]播放次数为[{play_count}]")
        if average_play + self.balance_limit >= play_count:
            log.write(f"歌曲[{song_name}]在平衡范围内,允许播放",3)
            return True
        else:
            log.write(f"歌曲[{song_name}]触发平衡播放保护,不允许播放",3)
            return False

    def get_song(self, song_name: str) ->dict | None:
        """
        读取指定song的所有数据，返回该song行的所有字段内容。
        :param song_name: 歌曲名(非路径)
        :return: dict 或 None（未找到时）
        """
        if not self.is_ok:
            return None
        try:
            self.cursor.execute("SELECT * FROM songs WHERE SongName = ?", (song_name,))
            self.db.commit()
            row = self.cursor.fetchone()
            if row:
                columns = [desc[0] for desc in self.cursor.description]
                info = dict(zip(columns, row))
                log.write(f"获取到[{song_name}]的数据为[{info}]")
                return info
            else:
                log.write(f"获取[{song_name}]数据时失败",2)
                return None
        except Exception as e:
            log.write(f"读取歌曲[{song_name}]数据时发生错误: {e}", 1)
            return None
    
    def get_artist(self,song_info,song_path: str) -> str:   # 类型检查器何一未?
        if song_info is None:
            return "Unknown"
        song_type = os.path.splitext(song_path)[1].lower()
        if song_type == '.acc' or song_type == '.wav':
            return "Unknown"
        elif song_type == '.mp3':
            return song_info.get("TPE1",["Unknown"])[0].replace('/',';')
        elif song_type == '.flac' or song_type == '.ogg':
            return ";".join(song_info.get("artist",["Unknown"]))
        elif song_type == '.m4a':
            return ";".join(song_info.get("©ART",["Unknown"])[0].split('/'))
        elif song_type == '.wma':
            return ";".join(str(artist) for artist in song_info.get("Author",["Unknown"]))
        return "Unknown"

    def add_song(self, song_path: str) -> None:
        """
        添加新song数据到数据库。
        :param song_name: 歌曲名
        :param duration: 歌曲时长（秒）
        :param artists: 艺术家列表字符串
        """
        if not self.is_ok:
            return None
        try:
            song_info = File(song_path)
            if not song_info:
                return
            song_name = self.path_to_name(song_path)
            artist = self.get_artist(song_info,song_path)
            duration = song_info.info.length
            self.cursor.execute(
                "INSERT INTO songs (SongName, Duration, Artists, PlayCount, LoopCount, FirstPlay, LastPlay) VALUES (?, ?, ?, 0, 0, ?, ?)",
                (song_name, duration, artist, int(time.time()), int(time.time()))
            )
            self.db.commit()
            log.write(f"添加歌曲[{song_name}]到数据库", 3)
        except Exception as e:
            log.write(f"添加歌曲[{song_name}]数据时发生错误: {e}", 1)

    def check_song(self,song_path: str) ->None:
        """
        检查并更新同名歌曲的数据
        """
        song_name = self.path_to_name(song_path)
        song_info = File(song_path)
        db_song_info = self.get_song(song_name)
        if not db_song_info or not song_info:
            return None
        
        artist = self.get_artist(song_info,song_path)
        duration = song_info.info.length

        if db_song_info["Artists"] != artist:
            self.cursor.execute(
                "UPDATE songs SET Artists = ? WHERE SongName = ?",
                (artist, song_name)
            )
            self.db.commit()
        
        if db_song_info["Duration"] != duration:
            self.cursor.execute(
                "UPDATE songs SET Duration = ? WHERE SongName = ?",
                (duration, song_name)
            )
            self.db.commit()

    def count_song(self, song_path: str) -> None:
        """
        更新song的播放数据（PlayCount、LastPlay、LoopCount）。
        :param song_name: 歌曲名
        """
        global is_loop
        if not self.is_ok:
            return None
        
        self.check_song(song_path) # 检查数据

        song_name = self.path_to_name(song_path)
        if song_name not in self.day_data["song"]:
            self.day_data["song"][song_name] = [0,0] # [播放次数,循环播放次数]
        self.day_data["song"][song_name][0] += 1
        if is_loop:
            self.day_data["song"][song_name][1] += 1
        log.write(f"当前日数据为[{self.day_data}]")

        try:
            song_data = self.get_song(song_name)
            if song_data:
                new_play_count = song_data["PlayCount"] + 1
                new_last_play = int(time.time())
                new_loop_count = song_data["LoopCount"] + 1 if is_loop else song_data["LoopCount"]
                self.cursor.execute(
                    "UPDATE songs SET PlayCount = ?, LastPlay = ?, LoopCount = ? WHERE SongName = ?",
                    (new_play_count, new_last_play, new_loop_count, song_name)
                )
                self.db.commit()
                log.write(f"更新歌曲[{song_name}]播放数据", 3)
            else:
                log.write(f"歌曲[{song_name}]未找到,将自动添加", 3)
        except Exception as e:
            log.write(f"更新歌曲[{song_name}]播放数据时发生错误: {e}", 1)
        
        if is_loop and self.is_loop_balance:
            return None
        self.all_song_play_count += 1

    def get_start_time(self) ->None:
        if not self.is_ok:
            return None
        self.start_time = time.time()
        self.is_useful = True
    
    def get_end_time(self) ->None:
        if not self.is_ok:
            return None
        
        if not self.is_useful:
            log.write("未获取开始时间,无法记录结束时间",2)
            return None
        
        t = time.time()
        today = time.strftime("%Y%m%d")
        duration = int(t - self.start_time)
        log.write(f"本次记录播放时长为[{duration}]")
        self.times += duration

        if self.today == today: # 如果是同日
            return None
        # 跨日期
        self.write(day_change=True)
        self.read()
    
    def read(self) ->None:            
        """读取文件"""
        try:
            main_file_path = os.path.normpath(os.path.join(self.path,"main.json"))
            with open(main_file_path,"r",encoding=self.encode) as f:
                self.main_data = json.load(f)
                log.write("读取数据[main.json]")
        except FileNotFoundError:
            log.write("数据文件[main.json]不存在,将创建",2)
        except Exception as e:
            log.write(f"处理[main.json]时发生未知错误[{e}],数据记录功能关闭",1)
            self.is_ok = False

            
        try:
            day_file_path = os.path.normpath(os.path.join(self.path,f"Days/{get_gura_day()}.json"))
            with open(day_file_path,"r",encoding=self.encode) as f:
                self.day_data = json.load(f)
                log.write(f"读取数据[{get_gura_day()}.json]")
        except FileNotFoundError:
            log.write(f"数据文件[{get_gura_day()}.json]不存在,将创建",2)
            pass
        except Exception as e:
            log.write(f"处理[{get_gura_day()}.json]时发生未知错误[{e}],数据记录功能关闭",1)
            self.is_ok = False
    
    def loop_count_fix(self,song_path: str) ->  None:
        """
        修复循环播放时造成的首次播放时播放循环播放次数也记录
        """
        song_name = self.path_to_name(song_path)
        if song_name not in self.day_data["song"]:
            return None # 可确定 self.count()是先执行的,故本歌数据应比在
        self.day_data["song"][song_name][1] -= 1
        song_info = self.get_song(song_name)
        if not song_info:
            return None
        fix_loop_count = song_info["LoopCount"] - 1
        self.cursor.execute(
                    "UPDATE songs SET LoopCount = ? WHERE SongName = ?",
                    (fix_loop_count, song_name)
                )
        self.db.commit()
        log.write(f"[{song_name}]的循环播放次数已修复")

    def write(self,day_change: bool = False) -> None:
        """最后写入"""
        if not self.is_ok:
            return None # 如果程序未能记录数据
        
        self.day_data["all"] += self.times
        self.main_data["all"] += self.times

        if self.today[:4] not in self.main_data["year"]:   #如果当前数据不存在
            self.main_data["year"][self.today[:4]] = 0
        self.main_data["year"][self.today[:4]] += self.times

        if self.today[:6] not in self.main_data["month"]:
            self.main_data["month"][self.today[:6]] = 0
        self.main_data["month"][self.today[:6]] += self.times

        if day_change:
            log.write("检测到日期跨越,将重新加载数据",3)
            yester_gura_day = get_gura_day(self.today)
            self.end_write(yester_gura_day)
            self.today = time.strftime("%Y%m%d")
            self.read()
    
    def end_write(self,gura_day: int | None = None) ->None:
        if not gura_day: # 默认日期
            gura_day = get_gura_day()
        main_file_path = os.path.normpath(os.path.join(self.path,"main.json"))
        try:
            with open(main_file_path,"w",encoding=self.encode) as file:
                log.write(f"写入文件[main.json]内容为[{self.main_data}]")
                json.dump(self.main_data,file,indent=4,ensure_ascii=False)
        except Exception as e:
            log.write(f"在写入[main.json]时发生错误[{e}]",1)

        day_file_path = os.path.normpath(os.path.join(self.path,f"Days/{gura_day}.json"))
        try:
            with open(day_file_path,"w",encoding=self.encode) as file:
                log.write(f"写入文件[{gura_day}.json]内容为[{self.day_data}]")
                json.dump(self.day_data,file,indent=4,ensure_ascii=False)
        except Exception as e:
            log.write(f"在写入[{gura_day}.json]时发生错误[{e}]",1)

    def close(self) ->None:
        """关闭数据统计"""
        self.write()
        self.db.commit()
        self.cursor.close()
        self.db.close()

class logs:
    obj = None
    def __new__(cls):
        if cls.obj == None:
            cls.obj = super().__new__(cls)
        
        return cls.obj
    
    def __init__(self):
        self.path = os.path.normpath(os.path.join(main_path,"log/"))
        if not os.path.exists(self.path):
            os.makedirs(self.path,exist_ok=True)
        self.already_init = False
        self.levers = {4:"Debug",3:"Info ",2:"Warn ",1:"Error",0:"Panic"}

    def init(self,levers: int =4) ->None:
        """初始化日志"""
        if self.already_init:
            return None
        if not os.path.exists(self.path):
            os.makedirs(self.path,exist_ok=True)

        file_path = os.path.normpath(os.path.join(self.path,f"{get_gura_day()}-{time.strftime('%H%M%S')}.wan"))
        self.file = os.open(file_path,os.O_WRONLY | os.O_CREAT)
        os.write(self.file,"     *Thank You For Your Use*\n\n".encode())
        self.write_lever = levers
        self.logs_on = True
        self.already_init = True
        self.del_old()
    
    def write(self,content: str,lever: int =4) ->None:
        """写入内容"""
        if self.logs_on == False:
            return None
        if self.write_lever < lever:
            return None
        lev = self.levers.get(lever,"Debug")
        t = time.strftime("%H:%M:%S")
        txt = f"[{t} {lev}] |{content}\n"
        os.write(self.file,txt.encode())
        if not running_environment:
            print(txt,end='')

    def del_old(self):
        try:
            log_list: list = os.listdir(self.path)
            files = [file_name for file_name in log_list if os.path.splitext(file_name)[1] == ".wan"]
            current_log_name = f"{get_gura_day()}-{time.strftime('%H%M%S')}.wan"
            if current_log_name in files:
                files.remove(current_log_name)
            files.sort()

            while len(files) > 10:
                log_wan = files[0]
                os.remove(os.path.normpath(os.path.join(self.path,log_wan)))
                files.remove(log_wan)
        except Exception as e:
            self.write(f"清理日志文件时发生错误: {e}",2)

    def change_lever(self,lev: int) ->None:
        self.write_lever = lev if 0<= lev <= 4 else 4

    def close(self) ->None:
        """关闭日志"""
        self.write("日志关闭",3)
        self.logs_on = False
        os.close(self.file)

class config_manage(): #配置控制
    obj = None
    data = {
        "音乐文件夹路径": [],  # 支持多个路径
        "随机播放": (True, False),  # (启用, 是否真随机)
        "定时播放": 0,  # 0 为无限，单位分钟
        "播完暂停": True,
        "平衡播放": True,
        "平衡播放限度": 1,
        "循环播放不计入平衡播放": True,
        "伪随机可重复曲数": -1,
        "按键管理": {
            "暂停": "<ctrl>+<alt>+p",
            "退出": "<ctrl>+<alt>+s",
            "音量+": "<ctrl>+<alt>+<up>",
            "音量-": "<ctrl>+<alt>+<down>",
            "上一曲": "<ctrl>+<alt>+<left>",
            "下一曲": "<ctrl>+<alt>+<right>",
            "单曲循环": "<ctrl>+<alt>+l",
        },
        "音量变化值": 0.05,
        "音量初始值":0.8,
        "日志等级":3,
    }

    def __new__(cls):
        """单例模式"""
        if cls.obj is None:
            cls.obj = super().__new__(cls)
        return cls.obj
    
    def __init__(self):
        log.write("初始化config_manage类")
        self.data = config_manage.data
    
    def config_read(self) ->dict:
        """读取配置"""
        log.write("读取配置文件",3)
        try:
            with open("config.json",'r',encoding='utf-8') as file:
                self.data = json.load(file)
                self.data = self.updata(self.data)
        except FileNotFoundError: # 处理文件不存在的情况
            log.write("配置文件不存在,尝试创建",2)
            self.write(self.data) 
            
        return self.data
    
    @classmethod
    def write(cls,data: dict,file_name: str="config.json") ->None:
        log.write(f"写入文件[{file_name}],写入内容[{data}]")
        with open(file_name,'w',encoding='utf-8') as file:
            json.dump(data,file,indent=4,ensure_ascii=False)

    @classmethod
    def updata(cls,read_data: dict) ->dict:
        is_updata = False
        log.write("校对配置文件版本")
        for i in cls.data.keys():
            log.write(f"正在校对配置项[{i}]")
            if i in read_data:
                continue
            else:
                log.write(f"配置项[{i}]不存在,将执行重写操作",2)
                read_data[i] = cls.data[i] #补充值
                is_updata = True
        
        if is_updata is True:
            log.write("更新配置文件",3)
            cls.write(read_data)
        
        return read_data

    def change(self,config_name: str, config_set: Any) ->None:
        """修改配置"""
        log.write(f"修改配置项[{config_name}]值为[{config_set}]",3)
        if config_name not in config_manage.data:
            log.write(f"未知配置项[{config_name}]试图修改,已拒绝",2)
            return None
        self.data[config_name] = config_set
        self.write(self.data)

class player:
    obj = None
    def __new__(cls,cfg):
        if cls.obj == None:
            cls.obj = super().__new__(cls)
        
        return cls.obj

    def __init__(self,cfg):
        log.write("初始化player类")
        self.stop = False
        self.volume = float(cfg["音量初始值"])
        self.__music_pause = False
        self.change_value = cfg["音量变化值"]
        self.play_time = float(cfg["定时播放"]) *60
        self.after_play_stop = cfg["播完暂停"]
        self.now_time = 0
        self.need_stop = False
        self.fist_play = True
        self.next_stop = False
        if self.play_time <= 0:
            self.need_stop = False
        else:
            self.need_stop = True

    def play(self,path: str) ->None:
        try:
            log.write(f"加载音乐[{path}]",3)
            pygame.mixer.music.load(path)
            Data.get_start_time()
            pygame.mixer.music.play(loops=0)
        except pygame.error:
            log.write(f"加载[{path}]时失败",1)
            return None
        if self.fist_play and self.need_stop:
            log.write("第一次开始播放音乐")
            self.start_time = time.time()
            self.end_time = self.start_time + self.play_time
            log.write(f"预计定时播放停止时间[{self.end_time}]")
            self.fist_play = False

        if self.next_stop:
            log.write("自定义播放时长已到,播放停止",3)
            stop()

        while running and (pygame.mixer.music.get_busy() or self.__music_pause):
            if is_pause and not self.__music_pause:  #暂停
                log.write("暂停播放",3)
                Data.get_end_time()
                pygame.mixer.music.pause()
                self.__music_pause = True
            
            elif not is_pause and self.__music_pause:  #继续
                log.write("继续播放",3)
                pygame.mixer.music.unpause()
                Data.get_start_time()
                self.__music_pause = False
            
            if self.stop:
                Data.get_end_time()
                pygame.mixer.music.pause()
                pygame.mixer.music.unload()
                self.stop = False
                log.write(f"音乐[{path}]中止播放")
                return None
            
            if self.need_stop and not self.next_stop:
                self.now_time = time.time()
                if self.now_time >= self.end_time:
                    log.write("定时播放设定时间已到",3)
                    if  not self.after_play_stop:
                        stop()
                    elif self.after_play_stop:
                        log.write("下一曲将停止播放")
                        self.next_stop = True
                
            time.sleep(0.1)

        if running:
            Data.get_end_time()
            log.write(f"记录歌曲[{path}]播放次数")
            Data.count_song(path)

    def volume_change(self,setting: str) ->None:
        """调节音量"""
        delta = self.change_value if setting == "up" else -self.change_value
        self.volume = max(0.0, min(1.0, self.volume + delta))
        log.write(f"调整音量为[{self.volume}]",3)
        pygame.mixer.music.set_volume(self.volume)

    def change_song(self,song: str) -> None:
        """切换歌曲"""
        global message,Lock
        log.write(f"将切换歌曲[{song}]")
        self.stop = True
        with Lock:
            message = song
    
    def loop(self):
        global is_loop
        is_loop = not is_loop
        log.write(f"将单曲循环状态变更为[{is_loop}]",3)

class for_songs:
    def __init__(self,cfg: dict):
        log.write("初始化for_songs类")
        self.music = 0
        self.music_list: list[str] = []
        self.true_list = []
        self.true_random_play_again = 3
        self.balance_play = cfg["平衡播放"],
        self.accept_same = cfg["伪随机可重复曲数"] if cfg["伪随机可重复曲数"] >= -1 else -1

    def player(self) ->None:
        global message,music_play_list,Lock
        del(music_play_list)
        first_play = False
        fix_already = False
        n = len(self.music_list)
        if n <= 0:
            log.write("播放列表未生成,拒绝调用",1)
            stop()
        
        while running:
            if self.balance_play and (not first_play):
                if Data.balance_play(self.music_list[self.music]) and (not is_loop):
                    log.write(f"接下来播放音乐[{Data.path_to_name(self.music_list[self.music])}]")
                    MusicPlayer.play(self.music_list[self.music])
                
                elif is_loop:
                    log.write(f"正在循环播放音乐[{Data.path_to_name(self.music_list[self.music])}]")
                    if not fix_already:
                        log.write("修复循环播放次数")
                        Data.loop_count_fix(self.music_list[self.music])
                        fix_already = True
                    MusicPlayer.play(self.music_list[self.music])

                else:
                    log.write(f"歌曲[{Data.path_to_name(self.music_list[self.music])}]触发保护,跳过播放")
            else:
                log.write(f"接下来播放音乐[{Data.path_to_name(self.music_list[self.music])}]")
                first_play = False
                MusicPlayer.play(self.music_list[self.music])

            with Lock:
                if message == "last":
                    log.write(f"收到切歌消息[{message}]")
                    self.music = (self.music-1) % n #递减环绕
                    message = None
                    first_play = True
                    fix_already = False
                    continue

                elif message == "next":
                    log.write(f"收到切歌消息[{message}]")
                    self.music = (self.music+1) % n
                    message = None
                    first_play = True
                    fix_already = False
                    continue

            if is_loop:
                continue
            
            self.music = (self.music+1) % n
            fix_already = False

    def list_play(self,music_path: list) ->None:
        log.write("生成顺序播放列表",3)
        self.music_list = music_path
        log.write(f"顺序播放列表为[{self.music_list}]")
        self.player()

    def true_random_play(self,music_path: list) ->None:
        global message,Lock
        log.write("开始真随机播放",3)
        self.music_list = music_path
        n = len(self.music_list)
        self.music = random.randint(0,n-1)

        while running:
            log.write(f"选取接下来播放音乐为[{Data.path_to_name(self.music_list[self.music])}]")
            MusicPlayer.play(self.music_list[self.music])
            with Lock:
                if message != None:
                    log.write(f"收到切歌消息[{message}]")
                    message = None
                    if is_loop:
                        self.music = random.randint(0,n-1)
                        continue
            if is_loop:
                continue
            self.music = random.randint(0,n-1)

    def false_random_play(self,music_path: list) ->None:
        log.write("准备伪随机播放",3)
        n = len(music_path)
        music_set = set(range(n))
        again_play = random.randint(max(1, n//10), max(1, n//5))
        if self.accept_same >= 0:
            again_play = self.accept_same
        again_play_dict = {}

        log.write(f"生成可重复歌曲列表,歌曲数量为[{again_play}],可重复次数为[{self.true_random_play_again}]")
        while len(again_play_dict) < again_play:
            nm = random.choice(music_path)
            if nm in again_play_dict:
                continue
            log.write(f"选中歌曲[{nm}]为可重复歌曲")
            again_play_dict[nm] = 0

        log.write("开始生成伪随机播放列表",3)
        while music_set:
            m = random.choice(list(music_set))  # 每次临时转换
            nnn = music_path[m]
            self.music_list.append(nnn)
            log.write(f"选中歌曲[{nnn}]")
            
            if nnn in again_play_dict and again_play_dict[nnn] < self.true_random_play_again:
                log.write(f"歌曲[{nnn}]已重复[{again_play_dict[nnn]}次]")
                again_play_dict[nnn] += 1
                continue
            
            log.write(f"移除候选歌曲[{nnn}]")
            music_set.remove(m)
            
        log.write("开始伪随机播放",3)
        self.player()


def get_gura_day(day: str | None = None) -> int:
    today = day if day else time.strftime("%Y%m%d")
    day_start = time.mktime(time.strptime("20250501","%Y%m%d"))
    day_today = time.mktime(time.strptime(today,"%Y%m%d"))
    duration = (day_today - day_start) // (24*60*60)
    return int(duration)

def pause() ->None: #暂停
    global is_pause
    log.write(f"暂停函数被调用,当前状态[{is_pause}]",3)
    is_pause = not is_pause

def stop() -> None:
    global is_pause, running
    running = False

    if Data != None:
        log.write("结束统计器")
        Data.get_end_time()
        Data.write()
        Data.end_write()

    # 停止音乐播放
    log.write("音乐播放停止",3)
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    

    # 停止监听器
    log.write("监听器停止")
    if listener != None:
        if listener.is_alive():
            log.write("停止按键监听")
            listener.stop()
    else:
        log.write("监听器不存在",2)
    log.write("程序即将关闭",3)
    time.sleep(0.3)
    log.close()
    os._exit(0)  # 0 表示正常退出

def summon_music_path(main_paths: list) -> list:
    log.write("开始生成音乐文件路径",3)
    exts = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma"}
    files = []
    for folder in main_paths:
        if not os.path.isdir(folder):
            log.write(f"父路径[folder]无效",2)
            continue
        for root, _, file_names in os.walk(folder):
            for name in file_names:
                if os.path.splitext(name)[1].lower() in exts:
                    log.write(f"添加音乐文件[{name}]")
                    mus = os.path.normpath(os.path.join(root, name))
                    files.append(mus)
                    Data.add_num(mus)
    
    Data.set_n(len(files))
    return files

def create_hotkeys(config) -> dict:
    log.write("生成按键监测字典")
    need_updata = False
    required_keys = ["暂停", "退出", "音量+", "音量-", "上一曲", "下一曲","单曲循环"]
    for key in required_keys:
        if key not in config:
            config[key] = config_manage.data["按键管理"][key]
            Configer.change("按键管理", config)
            log.write(f"按键监听缺失键[{key}],已修改",2)
            need_updata = True

    if need_updata:
        Configer.change("按键管理",config)
    _dict = {
        config["暂停"]: lambda: pause(),
        config["退出"]: lambda: stop(),
        config["音量+"]: lambda: MusicPlayer.volume_change("up"),
        config["音量-"]: lambda: MusicPlayer.volume_change("down"),
        config["上一曲"]: lambda: MusicPlayer.change_song("last"),
        config["下一曲"]: lambda: MusicPlayer.change_song("next"),
        config["单曲循环"]: lambda: MusicPlayer.loop(),
    }
    log.write(f"返回监听字典[{_dict}]")
    return _dict

atexit.register(stop)

log = logs()
log.init(3)
Configer = config_manage()
config: dict = Configer.config_read() #读取配置
_lever = config["日志等级"]
if 4 < _lever or _lever < 0:
    log.write("日志等级错误,拒绝更改",2)
else:
    log.change_lever(_lever)
Data = DataManage(cfg=config)

MusicPlayer = player(config)
MusicList = for_songs(config)

l_dict = create_hotkeys(config["按键管理"])
log.write("初始化按键监听")
listener = keyboard.GlobalHotKeys(l_dict)
log.write("开启按键监听",3)
listener.start()

def main():
    music_play_list: list = summon_music_path(config["音乐文件夹路径"])
    if music_play_list == []:
        log.write("未获取到音乐文件夹路径,将退出程序",1)
        stop()
    play_method: tuple = config["随机播放"]
    if play_method[0] == True:
        if play_method[1] == True:
            MusicList.true_random_play(music_play_list)
        elif play_method[1] == False:
            MusicList.false_random_play(music_play_list)
        else:
            log.write(f"播放模式错误,将退出程序,当前播放模式设置为[{play_method}]",1)
            stop()
    elif play_method[0] == False:
        MusicList.list_play(music_play_list)
    
    else:
        log.write(f"播放模式错误,将退出程序,当前播放模式设置为[{play_method}]",1)
        stop()

if __name__ == "__main__":
    main()