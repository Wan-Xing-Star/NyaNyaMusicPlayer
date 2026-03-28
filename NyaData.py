from flask import Flask,render_template
import os,sys,time,atexit,sqlite3,json,webbrowser,threading



main_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
app = Flask(__name__)


def stop():
    os._exit(0)

atexit.register(stop)


class DataManage:
    def __init__(self) -> None:
        self.encode = 'utf-8'
        self.month_list = ["01","02","03","04","05","06","07","08","09","10","11","12"]
        self.path = os.path.normpath(os.path.join(main_path,"data/"))
        if not os.path.exists(self.path):
            os.makedirs(self.path,exist_ok=True)
        self.main_data = {}
        self.read_main()
        self.today = time.strftime("%Y%m%d")
        try:
            self.db = sqlite3.connect(os.path.normpath(os.path.join(self.path,"main.db")))
        except Exception:
            stop()
        self.cursor = self.db.cursor()
    
    def read_main(self):
        try:
            main_file_path = os.path.normpath(os.path.join(self.path,"main.json"))
            with open(main_file_path,"r",encoding=self.encode) as f:
                self.main_data = json.load(f)
        except FileNotFoundError:
            stop()
        except Exception as e:
            self.is_ok = False
    
    def get_index_data(self) ->tuple:
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
        return tuple(data)










Data = DataManage()


@app.route("/")
def index():
    data = Data.get_index_data()
    year = data[0]
    duration = data[1]
    month = data[2]
    return render_template("NyaData.html",year=year,
                           total_hours=duration,
                           month_data=month)


def open_browser():
    webbrowser.open_new("http://127.0.0.1:1812/")

def main():
    threading.Timer(1, open_browser).start()
    app.run(port=1812)

if __name__ == "__main__":
    main()