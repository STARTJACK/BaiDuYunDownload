
#PanParse1.0
#百度云解析，适合有提取码,无提取码,单文件和文件夹的解析
#暂不支持登陆
#文件夹文件过多的情况无法进行批量打包
#下载功能可用

#虚线内的设置固定不变，请勿擅自更改
#----------------------------------------------------------------------------------------------------------------------------------------------#
HOME_URL='https://pan.baidu.com/disk/home'
VCODE_URL='https://pan.baidu.com/api/getvcode?prod=pan&t=0.2664991526027676&channel=chunlei&web=1&app_id=250528&bdstoken=ac934e07a2656639a08f71bd04d9f72c&logid=MTUzMzU0MjM1NTI4MTAuMTQyMzc1OTgwNjkyNTkxMjg=&clienttype=0'
VERIFY_SURL='https://pan.baidu.com/share/verify?surl=%s&%s&channel=chunlei&web=1&app_id=250528&bdstoken=null&logid=MTUzMzgwMjE5Mjg4NTAuNDMxMjA4MDA4MzMyMzY5Nw==&clienttype=0'
PARSE_URL='https://pan.baidu.com/api/sharedownload?sign=%s&timestamp=%s&channel=chunlei&web=1&app_id=%s&bdstoken=null&clienttype=0'
HOME_REAL_URL='http://d.pcs.baidu.com/rest/2.0/pcs/file?app_id=%s&method=locatedownload&path=%s&ver=4.0&time=%s'
SHARE_LIST_URL='https://pan.baidu.com/share/list?shareid=%s&uk=%s&dir=%s'

HEADERS={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Referer':None,
            'Cookie':None,
}

#下载可用User-Agent
User_Agent=[
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Mozilla/5.0 (Linux; U; Android 7.1.2) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.108 Quark/2.4.3.987 Mobile Safari/537.36',
            None, #发现无User-Agent一样能下载
        ]


#----------------------------------------------------------------------------------------------------------------------------------------------#


#用户设置项
MAX_NUM=64    #线程数
FILE_PATH="F:/Desktop/"  #文件下载路径（必须设置）
TEMP_PATH="F:/Desktop/FILE/Temp/"  #临时文件夹设置（必须设置）
Cookie='用户cookie'









