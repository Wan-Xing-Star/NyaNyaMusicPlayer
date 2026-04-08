from flask import Flask,render_template,request
import os,sys,time,atexit,sqlite3,json,webbrowser,threading


main_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
app = Flask(__name__,
            template_folder=os.path.normpath(os.path.join(main_path,"templates")),
            static_folder=os.path.normpath(os.path.join(main_path,"static")))


def stop():
    os._exit(0)

atexit.register(stop)

def get_gura_day(day: str | None = None) -> int:
    today = day if day else time.strftime("%Y%m%d")
    day_start = time.mktime(time.strptime("20250501","%Y%m%d"))
    day_today = time.mktime(time.strptime(today,"%Y%m%d"))
    duration = (day_today - day_start) // (24*60*60)
    return int(duration)

def get_ad_day(gura_day: str | int | None) -> str:
    if not gura_day:
        return time.strftime("%Y%m%d")
    day_start = time.mktime(time.strptime("20250501","%Y%m%d"))
    duration = int(gura_day) *60*60*24
    day_ad = time.gmtime(day_start + duration)
    return time.strftime("%Y%m%d",day_ad)


class DataManage:
    def __init__(self) -> None:
        self.encode = 'utf-8'
        self.month_list = ["01","02","03","04","05","06","07","08","09","10","11","12"]
        self.path = os.path.normpath(os.path.join(main_path,"data"))
        if not os.path.exists(self.path):
            os.makedirs(self.path,exist_ok=True)
        self.today = time.strftime("%Y%m%d")
        self.main_data = {}
        self.get_main_data()
        try:
            self.db = sqlite3.connect(
                f"file:{os.path.normpath(os.path.join(self.path, 'main.db'))}?mode=ro",
                uri=True,
                check_same_thread=False
            )
        except Exception:
            stop()
        self.cursor = self.db.cursor()
    
    def get_main_data(self):
        try:
            main_file_path = os.path.normpath(os.path.join(self.path,"main.json"))
            with open(main_file_path,"r",encoding=self.encode) as f:
                self.main_data = json.load(f)
        except FileNotFoundError:
            stop()
        except Exception as e:
            self.is_ok = False
    
    def get_song(self, song_name: str) ->dict | None:
        """
        读取指定song的所有数据，返回该song行的所有字段内容。
        :param song_name: 歌曲名(非路径)
        :return: dict 或 None（未找到时）
        """
        try:
            self.cursor.execute("SELECT * FROM songs WHERE SongName = ?", (song_name,))
            self.db.commit()
            row = self.cursor.fetchone()
            print(row)
            if row:
                columns = [desc[0] for desc in self.cursor.description]
                info = dict(zip(columns, row))
                return info
            else:
                return None
        except Exception as e:
            print(e)
            return None
        
    def get_all_data(self) ->list[tuple] | None:
        """
        获取所有歌曲数据\n
        -> list[tuple] | None
        """
        try:
            self.cursor.execute("SELECT * FROM songs")
            self.db.commit()
            return self.cursor.fetchall()
        except Exception as e:
            print(f"在获取所有数据时发生[{e}]错误")
            return None
    
    def get_day_data(self,gura_day: int) ->dict | None:
        """
        获取日听歌数据文件\n
        ->dict | None
        """
        try:
            with open(os.path.normpath(os.path.join(self.path,f"Days/{gura_day}.json"))) as file:
                data = json.load(file)
                if not data.get("all",0):
                    return None
                return data
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"在读取[{gura_day}.json]时出现错误[{e}]")

    def get_most_play_day(self,song_name: str,start_day: str|None = None, end_day: str|None = None) -> tuple | None:
        """
        day: AD day\n
        -> tuple(播放次数最多,循环播放最多)[Gura Day] | None
        """
        duration = [0,get_gura_day()]
        most_loop,most_play = 0,0
        most_loop_day,most_play_day = [],[]
        if not start_day:
            duration[0] = get_gura_day(start_day)
        if not end_day:
            duration[1] = get_gura_day(end_day)
        if not os.path.exists(os.path.normpath(os.path.join(self.path,"Days"))):
            os.makedirs(self.path,exist_ok=True)
            return None
        for day in range(duration[0],duration[1]+1):
            day_data = self.get_day_data(day)
            if not day_data:
                continue
            song_data: dict|None = day_data.get("song",None)
            if not song_data:
                continue
            song: list = song_data.get(song_name,None)
            if not song:
                continue
            if song[0] > most_play:
                most_play_day = [day]
                most_play = song[0]
            elif song[0] == most_play:
                most_play_day.append(day)
            if song[1] > most_loop:
                most_loop_day = [day]
                most_loop = song[1]
            elif song[1] == most_loop:
                most_loop_day.append(day)
        
        return (most_play_day,most_loop_day)



class ShowData(DataManage):
    def __init__(self) -> None:
        super().__init__()
    def index_data(self) ->list:
        """
        获取主页数据\n
        -> tuple\n
        [0] 今年年份\n
        [1] 总播放时长\n
        [2] 年内月播放时长(list)
        """
        if not self.main_data:
            stop()
        
        data: list = []
        year = self.today[:4]
        data.append(year)
        data.append(self.main_data["all"]//(60*60))
        month_data:list = []
        for month in self.month_list: # 获取12个月份
            month_data_get = self.main_data["month"].get(f"{year}{month}",0) // (60 * 60)
            month_data.append([month,month_data_get])
        
        data.append(month_data)
        return data

    def song_data(self,song_name) ->list | None:
        """
        获取指定歌曲数据\n
        ->list\n
        [0] 歌名\n
        [1] 时长\n
        [2] 作家\n
        [3] 播放次数\n
        [4] 单曲循环次数\n
        [5] 第一次播放日期\n
        [6] 上次播放日期\n
        [7] 播放最多的一天\n
        [8] 循环播放最多的一天
        """
        data = self.get_song(song_name)
        if not data:
            return None
        list_data = []
        for _ in data.keys():
            list_data.append(data.get(_,None))
        most_play = self.get_most_play_day(song_name)
        list_data.extend([None,None])
        if not most_play:
            return list_data
        for __ in range(len(most_play[0])):
            most_play[0][__] = get_ad_day(most_play[0][__])
        for __ in range(len(most_play[1])):
            most_play[1][__] = get_ad_day(most_play[1][__])
        list_data[7],list_data[8] = most_play[0],most_play[1]
        return list_data
    
    def day_data(self,ad_day: str) -> dict | None:
        """
        获取单日听歌数据\n
        -> dict | None\n
        "all": [int] 听歌时长\n
        "song": [dict] "song_name" : [list] [播放次数,循环播放次数]
        """
        day = get_gura_day(ad_day)
        return self.get_day_data(day)
    
    def all_song_data(self) -> list[tuple] | None:
        """
        获取所有歌曲数据\n
        -> list[tuple] | None
        """
        return self.get_all_data()

        

Show = ShowData()


@app.route("/")
def index():
    data = Show.index_data()
    return render_template("NyaData.html", all_data = data)

@app.route("/day")
def days():
    ad_day = request.args.get("day")
    if not ad_day: # 未获取到url中的日期 全部返回空值
        return render_template("NyaDay.html",day_total = None, day_each = None)
    data = Show.day_data(ad_day)
    if not data or (data.get("all",0)//60) < 1 : # 没有数据或者听歌时长小于1min时 #传值None
        return render_template("NyaDay.html",day_total = None, day_each = None)
    return render_template("NyaDay.html", day_total = data.get("all",0) // 60, day_each = data.get("song",None))

@app.route("/song")
def song():
    song_name = request.args.get("songname")
    if not song_name:
        return render_template("NyaSong.html",song_data= [None for __ in range(9)])
    print(song_name)
    data = Show.song_data(song_name)
    print(data)
    return render_template("NyaSong.html",song_data= data)


# @app.route("/AllSong")
# def AllSong():
#     data = Show.all_song_data()
#     # 如果是空值就返回空值本身
#     return

def open_browser():
    webbrowser.open_new("http://127.0.0.1:1812/")

def main():
    threading.Timer(1, open_browser).start()
    app.run(port=1812)

if __name__ == "__main__":
    main()