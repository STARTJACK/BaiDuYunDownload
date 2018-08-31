import json,time,re,requests,urllib,os
import settings , MultiThread
from queue import Queue

class BaiDuYun():
    #初始化各类数据(password、headers、cookie)
    def __init__(self):
        self.url_input = input("\n[ 请输入百度网盘链接 ]：")
        self.url_input=self.url_input.replace("http", "https") if self.url_input.find("https") == -1 else self.url_input #确保以https开头才能获得响应
        self.vcode_url=settings.VCODE_URL       #验证码获取地址
        self.surl = re.search(".*?1(.*)", self.url_input).group(1).split()[0]
        # print(self.surl)

        #headers构造
        self.vcode_headers =self.url_headers= self.file_headers=settings.HEADERS #验证码请求头
        self.url_headers['Referer']=self.url_input  #源地址请求头
        self.file_headers['Referer']=self.init_url="https://pan.baidu.com/share/init?surl=%s" % self.surl  #文件信息地址请求头

        #判断是否需要提取码
        self.judge_res=requests.get(self.url_input,headers=settings.HEADERS)
        self.judge_res.encoding="utf-8"
        if self.judge_res.text.find("提取密码")!=-1:
            self.judge=1             #标志需提取密码
            self.input_pwd()
        else:
            self.judge=0             #标志无需提取密码

    # 输入提取码并获取文件(夹)标识符
    def input_pwd(self):
        try:
            self.verify_surl = settings.VERIFY_SURL % (self.surl, time.time())  # 验证网址构造
            self.pwd = input("[ 请输入提取码 ]：")
            self.payload1 = {"pwd": self.pwd, }
            self.verify_res = requests.post(url=self.verify_surl, data=self.payload1, headers=self.file_headers).text
            # print(self.verify_res)
            self.cookie = re.search('.*"randsk":"(.*)"}', self.verify_res).group(1)  # 文件cookie标志符，用于登陆文件网址，在后面获得源地址时需post出去
            self.file_headers['Cookie'] = 'BDCLND=%s; ' % (self.cookie)
        except:
            print("!提取码错误,请重新输入!")
            self.input_pwd()

    # 获取源地址所需的必须参数
    def get_info(self):
        self.url_res = requests.get(self.url_input, headers=self.file_headers)
        self.url_res.encoding = "utf-8"
        self.sign = re.search('.*"sign":"(.*?)",', self.url_res.text).group(1)
        self.timestamp = re.search('"timestamp":(.*?),', self.url_res.text).group(1)
        self.fid_list = re.search('"fs_id":(.*?),', self.url_res.text).group(1)
        self.primaryid = re.search('"shareid":(.*?),', self.url_res.text).group(1)
        self.app_id = re.search('"app_id":"(.*?)",', self.url_res.text).group(1)
        self.uk = re.search('"uk":(.*?),', self.url_res.text).group(1)
        self.is_dir = int(re.search('"isdir":(.*?),', self.url_res.text).group(1))
        self.file_name=re.search('<title>(.*?)_免费高速',self.url_res.text).group(1)
        self.parent_path=re.search('"parent_path":"(.*?)",',self.url_res.text).group(1)


        #如果为文件夹，判断是下载文件夹还是单文件
        if self.is_dir:
            self.share_id = re.search('yunData.SHARE_ID = "(.*?)";', self.url_res.text).group(1)   #文件夹链接专有参数

            path=input("\n[ 输入文件路径 (若下载整个文件夹直接输入 /) ]：")
            dir = os.path.dirname(path)
            if dir!='/':
                self.share_list_url=settings.SHARE_LIST_URL %(self.share_id,self.uk,self.parent_path+urllib.parse.quote_plus(dir))
                res = requests.get(url=self.share_list_url, headers=settings.HEADERS).json()
                for data in res['list']:
                    if data['server_filename'] == os.path.basename(path):
                        self.fid_list = data['fs_id']
                        self.is_dir = data['isdir']
                        break
        # 判断文件或文件夹，解析出来的源地址不同
        self.type="nolimit" if self.is_dir==0 else "batch"
        self.source_url = settings.PARSE_URL % (self.sign, self.timestamp, self.app_id)  #源地址构造


    #获取验证码并显示
    def get_vcode(self):
        self.vcode_res = requests.get(self.vcode_url, headers=self.vcode_headers)
        self.image_url = json.loads(self.vcode_res.text)["img"]
        self.image_res = requests.get(self.image_url, headers=self.vcode_headers).content
        with open("Vcode.jpg","wb+") as f:
            f.write(self.image_res)
        os.system("start Vcode.jpg")
        self.vcode_input = input("[ 请输入验证码 ]：")
        os.remove("Vcode.jpg")

    def multi_thread_download(self,download_url):
        now = time.time()
        file_path = settings.FILE_PATH
        try:
            Location = requests.head(url=download_url).headers['Location']
            file_name = urllib.parse.unquote(re.search("&fin=(.*?)&", Location).group(1))
        except:
            # file_name="pack.zip"
            file_name = urllib.parse.unquote(re.search("zipname=(.*)", download_url).group(1))
        down = MultiThread.downloader(url=download_url, file_name=file_name,file_path=file_path)
        file_size=down.run()
        print("\n[ 文件下载完成  耗时 ]： %s 分钟   [ 平均速度 ]：%s MB/s    %s\n\n" % (round((time.time() - now)/60, 2), round(file_size / (time.time() - now), 2),time.asctime(time.localtime())))


    #真实地址解析
    def get_realurl(self):
        try:
            self.get_info()
            self.get_vcode()
            self.payload2 = {
                'encrypt': '0',
                'extra': '{"sekey":"%s"}' % urllib.parse.unquote(self.cookie) if self.judge==1 else None,    #注意此处需URL解码,有提取码需提交该参数
                'product': 'share',
                'vcode_input': self.vcode_input,
                'vcode_str': self.image_url.split("?")[1],
                'type': self.type,
                'uk': self.uk,
                'primaryid': self.primaryid,
                "fid_list": "[%s]" % self.fid_list,
                "path_list": None,
            }
            self.source_res = requests.post(url=self.source_url, data=self.payload2, headers=self.url_headers)
            # print(self.source_res.text)
            if self.source_res.text.find("dlink") == -1:
                print("  验证码错误！")
                self.get_realurl()
            else:
                dlink='"'+re.search('"dlink":"(.*?)"',self.source_res.text).group(1)+'"' #加双引号为了能被json解析，返回能直接使用的地址
                self.download_url=json.loads(dlink)
                if self.download_url.find("www.baidupcs.com")!=-1:
                    self.download_url=self.download_url+"&zipname=%s.zip"%(urllib.parse.quote(self.file_name))
                print("\n[ 下载链接为 ] ：[ %s ]"%self.download_url)
                try:
                    self.multi_thread_download(self.download_url)
                except Exception as result:
                    print("下载出错")
                    print("[ 错误信息 ]：",result)
        except:
            print("链接不存在")

class HomeDownLoad():
    def __init__(self):
        self.home_url=settings.HOME_URL
        self.headers=settings.HEADERS
        self.headers['Cookie']=settings.Cookie

    def get_realurl(self):
        i=0
        while i==0:
            try:
                self.path = input("\n[ 输入文件路径 (格式形如：/我的资源/1.mp4，仅支持单文件)]：")
                self.res = requests.get(url=self.home_url, headers=self.headers).text
                self.timestamp = re.search('"timestamp":(.*?),', self.res).group(1)
                self.home_real_url = settings.HOME_REAL_URL %(250528,urllib.parse.quote_plus(self.path),self.timestamp)
                self.real_res = requests.get(url=self.home_real_url, headers=self.headers).json()
                self.download_url = self.real_res['urls'][0]['url']
                print("\n[ 下载链接为 ]：%s"%self.download_url)
                self.download(self.download_url)
                i=1
            except Exception as result:
                print("  下载错误，请检查输入是否正确及网络情况")
                print("[ 错误信息 ]：",result)


    def download(self,download_url):
        now = time.time()
        file_path = settings.FILE_PATH
        file_name =os.path.basename(self.path)
        down = MultiThread.downloader(url=download_url, file_name=file_name, file_path=file_path)
        file_size = down.run()
        print("\n[ 文件下载完成  耗时 ]： %s 分钟   [ 平均速度 ]：%s MB/s    %s\n\n" % (
        round((time.time() - now) / 60, 2), round(file_size / (time.time() - now), 2), time.asctime(time.localtime())))


#主方法入口
if __name__ == '__main__':
    while True:
        chose=input("\n[ 个人网盘文件下载输入1，分享链接输入2 ]：")
        if chose=='1' or chose=='2':
            break
        else:
            print("[ 无法识别，请重新输入 ]")
    if chose==1:
        home = HomeDownLoad()
        home.get_realurl()
    else:
        baiduyun=BaiDuYun()
        baiduyun.get_realurl()
