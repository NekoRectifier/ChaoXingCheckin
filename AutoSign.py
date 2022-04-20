import requests
from lxml import etree
import base64
import re
import time
import yaml

config = {}
course_dict = {}
session = requests.session()
currClass = ''


def load_config():
    global config
    with open('config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)


def login(username, password):
    url = 'http://passport2.chaoxing.com/fanyalogin'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Referer': r'http://passport2.chaoxing.com/login?fid=&newversion=true&refer=http%3A%2F%2Fi.chaoxing.com'
    }

    data = {
        'fid': -1,
        'uname': username,
        'password': base64.b64encode(password.encode()).decode(),
        'refer': r'http%253A%252F%252Fi.chaoxing.com',
        't': True,
        'forbidotherlogin': 0
    }
    global session
    res = session.post(url, headers=headers, data=data)
    # print(res.cookies)


def get_class():
    url = 'http://mooc1-2.chaoxing.com/visit/courses'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
        'Referer': r'http://i.chaoxing.com/'

    }
    res = session.get(url, headers=headers)
    # print(res.text)

    if res.status_code == 200:
        class_HTML = etree.HTML(res.text)
        print("处理成功，您当前已开启的课程如下：")
        i = 0
        global course_dict

        for class_item in class_HTML.xpath("/html/body/div/div[2]/div[3]/ul/li[@class='courseItem curFile']"):
            # courseid=class_item.xpath("./input[@name='courseId']/@value")[0]
            # classid=class_item.xpath("./input[@name='classId']/@value")[0]
            try:
                class_item_name = class_item.xpath("./div[2]/h3/a/@title")[0]

                # 等待开课的课程由于尚未对应链接，所有缺少a标签。
                i += 1
                print(class_item_name)
                course_dict[i] = [class_item_name,
                                  "https://mooc1-2.chaoxing.com{}".format(class_item.xpath("./div[1]/a[1]/@href")[0])]
            except:
                pass
        print("———————————————————————————————————")
    else:
        print("error:课程处理失败")


def checkin(url: str):
    global currClass

    url = 'https://mobilelearn.chaoxing.com/widget/pcpick/stu/index?courseId={courseid}&jclassId={clazzid}'.format(
        courseid=re.findall(r"courseid=(.*?)&", url)[0], clazzid=re.findall(r"clazzid=(.*?)&", url)[0])
    # print(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0',
    }
    res = session.get(url, headers=headers)
    tree = etree.HTML(res.text)
    # fid=tree.xpath('/html/body/input[4]/@value')
    activeDetail = tree.xpath('/html/body/div[2]/div[2]/div/div/div/@onclick')
    if activeDetail:
        print('\n')
        print(course_dict[currClass][0] + "------检测到：" + str(len(activeDetail)) + "个活动。")
        time.sleep(config['sleep_time'])

        for activeID in activeDetail:
            global id
            id = re.findall(r'activeDetail\((.*?),', activeID)
            enc = ''
            data = session.get(
                'https://mobilelearn.chaoxing.com/v2/apis/sign/refreshQRCode?activeId={id}'.format(id=id[0])).json()[
                'data']

            if data is not None:
                enc = data['enc']
            print("current enc is: ", enc)

            url = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax?activeId={id}&clientip={ip}&latitude={lat}&longitude={lon}&appType=15&fid=0&enc={enc}&address={address}".format(
                id=id[0],
                ip=config['client_ip'],
                lat=config['lat'],
                lon=config['lon'],
                enc=enc,
                address=config['address'])

            res = session.get(url, headers=headers)
            # url='https://mobilelearn.chaoxing.com//widget/sign/pcStuSignController/checkSignCode?activeId={id}&signCode={signcode}'.format(id=id[0],signcode=1236)
            # res=session.get(url,headers=headers)
            # print(url)
            print('******************')
            print(res.text)
            if '非签到活动' in res.text:
                continue
        print('\n')


def main_handler():
    print("start")


if __name__ == '__main__':
    load_config()
    login(config['username'], config['password'])
    get_class()

    for currClass in course_dict:
        checkin(course_dict[currClass][1])
