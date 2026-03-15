#Python:3.13
import os,sys,json,random,time
import pygame #pip install pygame #2.6.1
from pynput import keyboard #pip install pynput #1.8.1
from mutagen import File #pip install mutagen #1.47.0

pygame.mixer.init() #初始化音乐播放器

is_pause = False
is_loop = False
running = True
listener = None #按键监听
Configer = None #配置类实例
MusicPlayer = None #播放类实例
log = None #日志类实例
Days = None #日期转换实例
Data = None #数据统计类实例
MusicList = None #播放列表管理类实例
data_path = os.path.normpath(os.path.join(os.getcwd(),"data/")) #数据文件夹目录
log_path = os.path.normpath(os.path.join(os.getcwd(),"log/"))
message = None #播放器消息传递
music_play_list = []

class data_manage:
    #data1 =>歌名:(听歌次数,单歌时长
    #data2 =>日,月,年听歌总时间
    obj = None
    def __init__(self):
        if not os.path.exists(data_path):
            log.write("统计文件夹缺失,已创建=data_manage.__init__",2)
            os.makedirs(data_path,exist_ok=True)
        
        self.encode = 'utf-8'
        self.data_1 = {}
        self.data_2 = {
            "all":0,
            "year":{},
            "month":{},
            "each_song":{}
            }
        self.data_2_read = {}
        self.today = time.strftime("%Y%m%d")
        self.today_gura = Days.ad_to_gura(self.today)
        self.file_name_1 = f"{self.today_gura}.json"
        self.file_name_2 = "main.json"
        self.path_1 = os.path.join(data_path,self.file_name_1)
        self.path_2 = os.path.join(data_path,self.file_name_2)
        self.start_time = 0
        self.get_start_time = False
        self.end_time = 0
        self.times = 0
    
    def __new__(cls):
        """单例模式"""
        if cls.obj is None:
            cls.obj = super().__new__(cls)
        return cls.obj
    
    def init(self):
        """自定义初始化"""
        log.write("初始化data_manage类=data_manage.init")
        self.read()

    def updata_2(self) -> None:
        for i in self.data_2.keys():
            log.write(f"正在检查[{i}]项=data_manage.updata_2")
            if i in self.data_2_read:
                continue
            log.write(f"[{i}]项不存在,已添加=data_manage.updata_2",2)
            self.data_2_read[i] = self.data_2[i]
        
        self.data_2 = self.data_2_read

    def format_duration(self,seconds):
        """
        将秒转换为 HH:MM:SS 或 MM:SS 格式
        """
        total_seconds = int(seconds)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        log.write(f"将[{seconds}]秒转换成[{hours:02d}:{minutes:02d}:{secs:02d}]格式化时间=data_manage.formate_duration")
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def get_time_s(self) ->None:
        """获取开始时间"""
        self.start_time = time.time()
        log.write(f"获取开始记录时间[{self.start_time}]=data_manage.get_time_s")
        self.get_start_time = True
    
    def get_time_e(self) ->None:
        """获取结束时间"""
        self.end_time = time.time()
        log.write(f"获取结束记录时间[{self.end_time}]=data_manage.get_time_e")
        if self.get_start_time == False:
            log.write("未获取到开始时间,无法计算,已跳过=data_manage.get_time_e",2)
            return None
        duration = (self.end_time - self.start_time)
        self.times = int(duration)
        log.write(f"计算本次播放时长为[{self.times}]=data_manage.get_time_e",3)

        log.write("将[all]值更改=data_manage.get_time_e")
        self.data_2["all"] += self.times

        self.today = time.strftime("%Y%m%d")

        if f"{self.today[:4]}" not in self.data_2["year"].keys():
            log.write(f"未获取到年份键值,已创建[{self.today[:4]}]=data_manage.get_time_e",2)
            self.data_2["year"][f"{self.today[:4]}"] = 0
        log.write(f"将[{self.today[:4]}]值更改=data_manage.get_time_e")
        self.data_2["year"][f"{self.today[:4]}"] += self.times

        if f"{self.today[:6]}" not in self.data_2["month"].keys():
            log.write(f"未获取到月份键值,已创建[{self.today[:6]}]=data_manage.get_time_e",2)
            self.data_2["month"][f"{self.today[:6]}"] = 0
        log.write(f"将[{self.today[:6]}]值更改=data_manage.get_time_e")
        self.data_2["month"][f"{self.today[:6]}"] += self.times
        self.get_start_time = False
        log.write("本次播放时长已记录",3)

    def count(self,path: str) ->None:
        music_name = os.path.splitext(os.path.split(path)[1])[0]
        if music_name not in self.data_1:
            self.data_1[music_name] = [0,(self.format_duration(File(path).info.length),File(path,easy=True).get('artist',['Unknown']))]
            log.write(f"创建统计数据[{music_name}]在单日数据中=data_manage.count",2)
        self.data_1[music_name][0] += 1
        log.write(f"变更统计数据[{music_name}->{self.data_1[music_name]}]=data_manage.count")

        if music_name not in self.data_2["each_song"].keys():
            log.write(f"创建统计数据[{music_name}]在总数据中=data_manage.count",2)
            self.data_2["each_song"][music_name] = [0,(self.format_duration(File(path).info.length),File(path,easy=True).get('artist',['Unknown']))]
        self.data_2["each_song"][music_name][0] +=1
        log.write(f"变更统计数据[{music_name}->{self.data_2["each_song"][music_name]}]=data_manage.count")

    def read(self) ->None:
        """读取文件"""
        try:
            with open(self.path_1,"r",encoding=self.encode) as f:
                self.data_1 = json.load(f)
                log.write(f"读取数据[{self.data_1}]=data_manage.open")
        except FileNotFoundError:
            log.write(f"数据文件[{self.path_1}]不存在,将创建=data_manage.open",2)
            pass
            
        try:
            with open(self.path_2,"r",encoding=self.encode) as f:
                self.data_2_read = json.load(f)
                log.write(f"读取数据[{self.data_2_read}]=data_manage.open")
                self.updata_2()
        except FileNotFoundError:
            log.write(f"数据文件[{self.path_2}]不存在,将创建=data_manage.open",2)
            pass

    def end_write(self) ->None:
        """最后写入"""
        with open(self.path_1,"w",encoding=self.encode) as file:
            log.write(f"写入文件[{self.path_1}]内容为[{self.data_1}]=data_manage.write")
            json.dump(self.data_1,file,indent=4,ensure_ascii=False)
        
        with open(self.path_2,"w",encoding=self.encode) as file:
            log.write(f"写入文件[{self.path_2}]内容为[{self.data_2}]=data_manage.write")
            json.dump(self.data_2,file,indent=4,ensure_ascii=False)

class days_change:
    start_day: str = "20250501"

    def get_month_days(self,year, month):
        """获取指定年份和月份的天数，考虑闰年"""
        if month == 2:
            # 闰年判断
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                return 29
            else:
                return 28
        elif month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        else:
            return 30

    def ad_to_gura(self,day):
        # 输入验证
        if len(day) != 8 or not day.isdigit():
            print("输入日期错误:日期格式应为YYYYMMDD")
            return 0 
        # 解析起始日期
        start_year = int(self.start_day[0:4])
        start_month = int(self.start_day[4:6])
        self.start_day_of_month = int(self.start_day[6:8]) 
        # 解析目标日期
        year = int(day[0:4])
        month = int(day[4:6])
        day_of_month = int(day[6:8])    
        # 验证日期有效性
        if not 1 <= month <= 12 or not 1 <= day_of_month <= 31:
            print("输入日期错误:月份或日期无效")
            return 0
        # 进一步验证日期的实际有效性
        max_day = self.get_month_days(year, month)
        if day_of_month > max_day:
            print(f"输入日期错误:{year}年{month}月最多有{max_day}天")
            return 0  
        # 检查日期是否早于起始日期
        if (year < start_year or 
            (year == start_year and month < start_month) or 
            (year == start_year and month == start_month and day_of_month < self.start_day_of_month)):
            print("输入日期早于起始日期")
            return 0
        # 如果是同一天，直接返回1（第1天）
        if year == start_year and month == start_month and day_of_month == self.start_day_of_month:
            return 1      
        gura_day: int = 0
        
        # 情况1:同一年份
        if year == start_year:
            # 情况1.1:同一个月
            if month == start_month:
                return day_of_month - self.start_day_of_month + 1           
            # 情况1.2:不同月份
            # 1) 先加上起始月份剩余的天数
            gura_day = self.get_month_days(start_year, start_month) - self.start_day_of_month + 1       
            # 2) 加上中间完整月份的天数
            for m in range(start_month + 1, month):
                gura_day += self.get_month_days(start_year, m)
            # 3) 加上目标月份的天数
            gura_day += day_of_month
            
            return gura_day      
        # 情况2:不同年份
        # 先计算起始年份剩余的天数
        # 1) 起始月份剩余的天数
        gura_day = self.get_month_days(start_year, start_month) - self.start_day_of_month + 1      
        # 2) 起始年份剩余月份的天数
        for m in range(start_month + 1, 13):
            gura_day += self.get_month_days(start_year, m)   
        # 3) 计算中间完整年份的天数（如果有）
        # 注意:这里是从 start_year+1 到 year-1，不包括year本身
        for y in range(start_year + 1, year):
            # 判断闰年
            if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0):
                gura_day += 366
            else:
                gura_day += 365  
        # 4) 计算目标年份的天数
        # a) 目标年份目标月份前的完整月份
        for m in range(1, month):
            gura_day += self.get_month_days(year, m)
        # b) 加上目标月份的天数
        gura_day += day_of_month     
        return gura_day

class logs:
    obj = None
    def __new__(cls):
        if cls.obj == None:
            cls.obj = super().__new__(cls)
        
        return cls.obj
    
    def __init__(self):
        self.already_init = False

    def init(self,levers: int =4) ->None:
        """初始化日志"""
        if self.already_init:
            return None
        if not os.path.exists(log_path):
            os.makedirs(log_path,exist_ok=True)

        file_path = os.path.normpath(os.path.join(log_path,f"{Days.ad_to_gura(time.strftime('%Y%m%d'))}-{time.strftime('%H%M%S')}.wan"))
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
        if lever == 4:
            lev = "[Debug]"
        elif lever == 3:
            lev = "[Info ]"
        elif lever == 2:
            lev = "[Warn ]"
        elif lever == 1:
            lev = "[Error]"
        elif lever == 0:
            lev = "[Panic]"
        t = time.strftime("%H:%M:%S")
        txt = f"{lev} {t}|{content}\n"
        b_txt = txt.encode()
        os.write(self.file,b_txt)

    def del_old(self):
        log_list: list = os.listdir(log_path)
        files = [file_name for file_name in log_list if os.path.splitext(file_name)[1] == ".wan"]
        
        files.sort()
        while len(files) >= 10:
            log_wan = files[0]
            os.remove(os.path.normpath(os.path.join(log_path,log_wan)))
            files.remove(log_wan)

    def change_lever(self,lev: int) ->None:
        self.write_lever = lev

    def close(self) ->None:
        """关闭日志"""
        self.write("日志关闭=logs.close",3)
        self.logs_on = False
        os.close(self.file)

class config_manage(): #配置控制
    obj = None
    data = {
        "音乐文件夹路径": [],  # 支持多个路径
        "随机播放": (True, False),  # (启用, 是否真随机)
        "定时播放": 0,  # 0 为无限，单位分钟
        "播完暂停": True,
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
        "音量初始值":1.0,
        "日志等级":3,
    }

    def __new__(cls):
        """单例模式"""
        if cls.obj is None:
            cls.obj = super().__new__(cls)
        return cls.obj
    
    def __init__(self):
        log.write("初始化config_manage类=config_manage.__init__")
        self.data = config_manage.data
    
    def config_read(self) ->dict:
        """读取配置"""
        log.write("读取配置文件=config_manage.config_read",3)
        try:
            with open("config.json",'r',encoding='utf-8') as file:
                self.data = json.load(file)
        except FileNotFoundError: # 处理文件不存在的情况
            log.write("配置文件不存在,尝试创建=config_manage.config_read",2)
            self.write(self.data) 

        self.data = self.updata(self.data)            
        return self.data
    
    @classmethod
    def write(cls,data: dict,file_name: str="config.json") ->None:
        log.write(f"写入文件[{file_name}],写入内容[{data}]=config_manage.write")
        with open(file_name,'w',encoding='utf-8') as file:
            json.dump(data,file,indent=4,ensure_ascii=False)

    @classmethod
    def updata(cls,read_data: dict) ->dict:
        is_updata = False
        log.write("校对配置文件版本=config_manage.updata")
        for i in cls.data.keys():
            log.write(f"正在校对配置项[{i}]")
            if i in read_data:
                continue
            else:
                log.write(f"配置项[{i}]不存在,将执行重写操作=config_manage.updata",2)
                read_data[i] = cls.data[i] #补充值
                is_updata = True
        
        if is_updata is True:
            log.write("更新配置文件=config_manage.updata",3)
            cls.write(read_data)
        
        return read_data

    def change(self,config_name: str, config_set: any) ->None:
        """修改配置"""
        log.write(f"修改配置项[{config_name}]值为[{config_set}]=config_manage.change",3)
        self.data[config_name] = config_set
        self.write(self.data)

class player:
    obj = None
    def __new__(cls,cfg):
        if cls.obj == None:
            cls.obj = super().__new__(cls)
        
        return cls.obj

    def __init__(self,cfg):
        log.write("初始化player类=player")
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
        global now_play 
        now_play = path
        try:
            log.write(f"加载音乐[{path}]=player.play",3)
            pygame.mixer.music.load(path)
            Data.get_time_s()
            pygame.mixer.music.play(loops=0)
        except pygame.error as e:
            log.write(f"加载[{path}]时失败=player.play",1)
            return None
        if self.fist_play == True:
            log.write("第一次开始播放音乐=player.play")
            self.start_time = time.time()
            self.end_time = self.start_time + self.play_time
            log.write(f"预计定时播放停止时间[{self.end_time}]=player.play")
            self.fist_play = False

        if self.next_stop == True:
            log.write("自定义播放时长已到,播放停止=player.play",3)
            stop()

        while running and (pygame.mixer.music.get_busy() or self.__music_pause):
            if is_pause and not self.__music_pause:  #暂停
                log.write("暂停播放=player.play",3)
                Data.get_time_e()
                pygame.mixer.music.pause()
                self.__music_pause = True
            
            elif not is_pause and self.__music_pause:  #继续
                log.write("继续播放=player.play",3)
                pygame.mixer.music.unpause()
                Data.get_time_s()
                self.__music_pause = False
            
            if self.stop == True:
                Data.get_time_e()
                pygame.mixer.music.pause()
                pygame.mixer.music.unload()
                self.stop = False
                log.write(f"音乐[{path}]中止播放=player.play")
                return None
            
            if self.need_stop == True:
                self.now_time = time.time()
                if self.now_time >= self.end_time:
                    log.write("定时播放设定时间已到=player.play",3)
                    if self.after_play_stop == False:
                        stop()
                    elif self.after_play_stop == True:
                        log.write("下一曲将停止播放=player.play")
                        self.next_stop = True
                
            time.sleep(0.1)

        if running:
            Data.get_time_e()
            log.write(f"记录歌曲[{path}]播放次数=player.play")
            Data.count(path)

    def volume_change(self,setting: str) ->None:
        """调节音量"""
        delta = self.change_value if setting == "up" else -self.change_value
        self.volume = max(0.0, min(1.0, self.volume + delta))
        log.write(f"调整音量为[{self.volume}]=player.volume_change",3)
        pygame.mixer.music.set_volume(self.volume)

    def change_song(self,song: str) -> None:
        """切换歌曲"""
        global message
        log.write(f"将切换歌曲[{song}]=player.change_song")
        self.stop = True
        message = song
    
    def loop(self):
        global is_loop
        is_loop = not is_loop

class for_songs:
    def __init__(self,cfg: dict):
        log.write("初始化for_songs类=for_songs.__init__")
        self.music = 0
        self.music_list = []
        self.true_random_play_again = 3

    def player(self) ->None:
        global message,music_play_list
        del(music_play_list)
        n = len(self.music_list)
        if n <= 0:
            log.write("播放列表未生成,拒绝调用=for_songs.player",1)
            stop()
        
        while running:
            MusicPlayer.play(self.music_list[self.music])
            if message == "last":
                log.write(f"收到切歌消息[message]=for_songs.player")
                self.music = (self.music-1) % n #递减环绕
                message = None
                continue

            elif message == "next":
                log.write(f"收到切歌消息[message]=for_songs.player")
                self.music = (self.music+1) % n
                message = None
                continue

            if is_loop:
                continue

            log.write(f"选取接下来播放音乐索引为[{self.music}]==for_songs.player")
            self.music = (self.music+1) % n

    def list_play(self,music_path: list) ->None:
        log.write("生成顺序播放列表=for_songs.list_play",3)
        self.music_list = music_path
        log.write(f"顺序播放列表为[{self.music_list}]=for_songs.list_play")
        self.player()

    def true_random_play(self,music_path: list) ->None:
        global message
        log.write("开始真随机播放=for_songs.true_random_play",3)
        self.music_list = music_path
        n = len(self.music_list)
        self.music = random.randint(0,n-1)

        while running:
            log.write(f"选取接下来播放音乐索引为[{self.music}]=for_songs.true_random_play")
            MusicPlayer.play(self.music_list[self.music])
            if message != None:
                log.write(f"收到切歌消息[message]=for_songs.true_random_play")
                message = None
                if is_loop:
                    self.music = random.randint(0,n-1)
                    continue
            if is_loop:
                continue
            self.music = random.randint(0,n-1)

    def false_random_play(self,music_path: list) ->None:
        log.write("准备伪随机播放=for_songs.false_random_play",3)
        n = len(music_path)
        music_set = set(range(n))
        again_play = random.randint(max(1, n//10), max(1, n//5))
        again_play_dict = {}

        log.write(f"生成运行重复歌曲列表,歌曲数量为[{again_play}],可重复次数为[{self.true_random_play_again}]=for_songs.false_random_play")
        while len(again_play_dict) < again_play:
            nm = random.choice(music_path)
            if nm in again_play_dict:
                continue
            log.write(f"选中歌曲[{nm}]为可重复歌曲=for_songs.false_random_play")
            again_play_dict[nm] = 0

        log.write("开始生成伪随机播放列表=for_songs.false_random_play",3)
        while music_set:
            m = random.choice(list(music_set))  # 每次临时转换
            nnn = music_path[m]
            self.music_list.append(nnn)
            log.write(f"选中歌曲[{nnn}]=for_songs.false_random_play")
            
            if nnn in again_play_dict and again_play_dict[nnn] < self.true_random_play_again:
                log.write(f"歌曲[{nnn}]已重复[{again_play_dict[nnn]}次]=for_songs.false_random_play")
                again_play_dict[nnn] += 1
                continue
            
            log.write(f"移除候选歌曲[{nnn}]=for_songs.false_random_play")
            music_set.remove(m)
            
        log.write("开始伪随机播放=for_songs.false_random_play",3)
        self.player()


def pause() ->None: #暂停
    global is_pause
    log.write(f"暂停函数被调用,当前状态[{is_pause}]=pause",3)
    is_pause = not is_pause

def stop() -> None:
    global is_pause, running
    running = False

    if Data != None:
        log.write("结束统计器=stop")
        Data.get_time_e()
        Data.end_write()

    # 停止音乐播放
    log.write("音乐播放停止=stop",3)
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    

    # 停止监听器
    log.write("监听器停止=stop")
    if listener != None:
        if listener.is_alive():
            log.write("停止按键监听=stop")
            listener.stop()
    else:
        log.write("监听器不存在=stop",2)
    log.write("程序即将关闭=stop",3)
    time.sleep(0.3)
    log.close()
    sys.exit(0)  # 0 表示正常退出

def summon_music_path(main_paths: list) -> list:
    log.write("开始生成音乐文件路径=summon_music_path",3)
    exts = {".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma"}
    files = []
    for folder in main_paths:
        if not os.path.isdir(folder):
            log.write(f"父路径[folder]无效=summon_music_path",2)
            continue
        for root, _, file_names in os.walk(folder):
            for name in file_names:
                if os.path.splitext(name)[1].lower() in exts:
                    log.write(f"添加音乐文件[{name}]=summon_music_path")
                    files.append(os.path.normpath(os.path.join(root, name)))
    return files

def create_hotkeys(config):
    log.write("生成按键监测字典=create_hotkeys")
    need_updata = False
    required_keys = ["暂停", "退出", "音量+", "音量-", "上一曲", "下一曲","单曲循环"]
    for key in required_keys:
        if key not in config:
            config[key] = config_manage.data["按键管理"][key]
            Configer.change("按键管理", config)
            log.write(f"按键监听缺失键[{key}],已修改=create_hotkeys",2)
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
    log.write(f"返回监听字典[{_dict}]=create_hotkeys")
    return _dict

Days = days_change()
log = logs()
log.init(3)
Configer = config_manage()
config: dict = Configer.config_read() #读取配置
_lever = config["日志等级"]
if 4 < _lever or _lever < 0:
    log.write("日志等级错误,拒绝更改=__main__",2)
else:
    log.change_lever(_lever)
Data = data_manage()
Data.init()

MusicPlayer = player(config)
MusicList = for_songs(config)

l_dict = create_hotkeys(config["按键管理"])
log.write("初始化按键监听=__main__")
listener = keyboard.GlobalHotKeys(l_dict)
log.write("开启按键监听=__main__",3)
listener.start()

def main():
    music_play_list: list = summon_music_path(config["音乐文件夹路径"])
    if music_play_list == []:
        log.write("未获取到音乐文件夹路径,将退出程序=main",1)
        stop()
    play_method: tuple = config["随机播放"]
    if play_method[0] == True:
        if play_method[1] == True:
            MusicList.true_random_play(music_play_list)
        elif play_method[1] == False:
            MusicList.false_random_play(music_play_list)
        else:
            log.write(f"播放模式错误,将退出程序,当前播放模式设置为[{play_method}]=main",1)
            stop()
    elif play_method[0] == False:
        MusicList.list_play(music_play_list)
    
    else:
        log.write(f"播放模式错误,将退出程序,当前播放模式设置为[{play_method}]=main",1)
        stop()

if __name__ == "__main__":
    main()