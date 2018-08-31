# -*- coding: utf-8 -*-
#多线程下载
import time,re,os,random,sys,threading,requests,settings,shutil
import urllib.request
from requests.packages import urllib3
from tempfile import  NamedTemporaryFile
from queue import Queue

class downloader(object):
    def __init__(self, url,  file_path,  file_name):
        self.User_Agent=settings.User_Agent
        self.url = url
        self.name = file_path+file_name
        self.file_name=file_name
        self.file_path=file_path
        try:
            self.req = urllib.request.Request(url=self.url)
            self.file_size = urllib.request.urlopen(self.req).headers['Content-Length']  # 获取响应头而不下载响应体，同时支持重定向
        except:
            self.file_size = requests.head(self.url, headers=settings.HEADERS).headers['Content-Length']
        self.total = int(self.file_size)
        self.queue=Queue()
        self.generate_list = set()        # 真实创建的线程列表
        self.lock=threading.Lock()     #用于显示进度
        self.blockNum=int(self.total/524288) +1 #每一块分为1M左右大小
        self.max_num = self.blockNum  if settings.MAX_NUM >self.blockNum else settings.MAX_NUM# 实际线程数
        # self.blockNum=1200
        self.numTag=0
        print("\n[ 线程数   ]：%s"%self.max_num)
        if self.total/1048576 >1024:
            print('[ 文件大小 ]：%s GB' % (round(self.total /1073741824, 2)))
        else:
            print('[ 文件大小 ]：%s MB'%(round(self.total/1048576,2)))
        print('[ 下载路径 ]：%s' % (self.file_path + self.file_name))
        try:
            shutil.rmtree(settings.TEMP_PATH+self.file_name)
        except :
            pass
        os.mkdir(settings.TEMP_PATH+self.file_name)


    # 划分每个下载块的范围
    def get_range(self):
        ranges=[ ]
        self.offset = int(self.total/self.blockNum)
        for i in range(self.blockNum):
            if i == self.blockNum-1:
                ranges.append(((i*self.offset+1),self.total-1))
            elif i==0:
                ranges.append((0,self.offset))
            else:
                ranges.append(((i*self.offset+1),(i+1)*self.offset))
        return ranges

    #进度显示
    def view_bar(self):
        with self.lock:
            self.numTag+=1
            rate_num = round(self.numTag / self.blockNum, 3)*100
            r = '\r[%s%s]' % ("-" * int(rate_num/2), "_" * (50 - int(rate_num/2)))  # 进度条封装
            sys.stdout.write(r)  # 显示进度条
            sys.stdout.write("%.2f"%rate_num + '%')  # 显示进度百分比
            sys.stdout.flush()  # 使输出变得平滑


    def download(self):
        if self.queue.empty() !=True:
            start,end,fileName=self.queue.get()
            urllib3.disable_warnings()
            finish = 0
            while finish ==0 :
                try:     #用于判断下载完成情况
                    try: #  用于判断网络错误
                        headers = {
                            'User-Agent': random.choices(self.User_Agent)[0],
                            'Range': 'bytes=%s-%s' % (start, end),
                        }
                        res= requests.get(self.url, headers=headers,timeout=90,verify=False).content #注意设置超时设置避免假死，此外requests默认allow_redirects = True，即自动解析重定向链接
                    except:
                        res=b''
                    if res.find(b'"error')!=-1 or res.find(b'"errno')!=-1:    #json错误
                        if res.find(b'time out') != -1:
                            print("连接超时")
                            res=b''
                            time.sleep(2)
                        else:
                            error=re.search(b'{.*"error.*?}.*',res,re.S).group(0)      #anti hotlinking及其他error/errno，注意可能含有换行符
                            res=res.replace(error,b'')
                            time.sleep(0.1)
                    elif res.find(b"<html>")!=-1 :             #网页错误文件
                        res=b''
                    if (end - start + 1) - len(res) ==0:      #下载完成标志
                        with open(fileName,"ab") as File:
                            File.seek(start)
                            File.write(res)
                            del res
                        self.view_bar()
                        finish=1
                        self.queue.task_done()     #若用queue.join()方法时，必须配合queue.task_done()，这样才能让队列任务消费完后不阻塞
                    else:
                        time.sleep(0.1)
                        raise KeyError #此处仅表示错误，无其他含义
                except:  #下载中断后将已下载部分写入文件中
                    size=len(res)
                    with open(fileName,"ab") as File:
                        File.write(res)
                    finish=0
                    start=start+size  #start<=end
                    if start>end:       #若start>end，将出现不断请求，程序不停止的情况
                        self.queue.task_done()
                        finish=1
                        self.view_bar()
                    else:
                        headers['Range']= 'bytes=%s-%s' % (start, end)
                        del res
            else:
                self.download()



    def run(self):
        with open(self.name,"w+") as f:
            pass
        print("\n|   开始下载文件   |\n")
        file_dir=settings.TEMP_PATH + self.file_name
        for ran in self.get_range():
            start,end = ran
            file= NamedTemporaryFile(dir=file_dir,delete=False)  #创建临时文件
            file.close()            #须将文件关闭才能操作文件
            fileName=file_dir+'/'+str(start)
            os.rename(file.name,fileName)
            items=(start,end,fileName)
            self.queue.put(items)
        for i in range(self.max_num):
            thread = threading.Thread(target=self.download)
            thread.start()
            self.generate_list.add(thread)
        for thread in self.generate_list:
            thread.join()
        self.queue.join()
        del self.generate_list
        print("\n\n|   文件块整合中   |")

        #文件块整合
        for i in os.listdir(file_dir):
            with open(self.name, "rb+") as f:   #此处注意，必须用rb+模式，才能保证文件指针方法seek()的指针位置是正确的
                f.seek(int(i))
                with open(file_dir+'/'+ str(i), "rb") as file:
                    f.write(file.read())
        shutil.rmtree(file_dir)
        return round(self.total/1048576,2)

if __name__ == '__main__':
    now = time.time()
    download_url = input("请输入下载链接：")
    file_path=settings.FILE_PATH
    # file_name = input("请输入文件名(包含后缀名)：")
    Location=requests.head(url=download_url).headers['Location']
    file_name = urllib.parse.unquote(re.search("&fin=(.*?)&",Location).group(1))
    down = downloader(url=download_url, file_path=file_path,file_name=file_name)
    file_size=down.run()
    print("[ 文件下载完成  耗时 ]： %s 分钟   [ 平均速度 ]：%s MB/s    %s\n\n" % (round((time.time() - now) / 60,2), file_size/(round((time.time() - now) / 60,2)),time.asctime(time.localtime())))


















