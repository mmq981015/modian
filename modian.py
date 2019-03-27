# -*- coding: utf-8 -*-
"""
摩点数据统计：多个项目的支持者
"""

import json
from time import sleep
import psycopg2
import requests
from lxml import etree

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Connection': 'keep-alive'
}
post_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/json',
    'Connection': 'keep-alive'
}


def get_simple_product(mid):
    '''
    请求摩点项目基础数据
    :param mid: 摩点项目id
    :return: 支持人数，支持总额
    '''
    url = 'https://zhongchou.modian.com/realtime/get_simple_product?ids={}'.format(mid)
    req = requests.get(url, headers=headers)
    txt = req.text
    start = len("window[decodeURIComponent(\'\')]([")
    end = len(txt) - 3
    js_txt = txt[start:end]
    js = json.loads(js_txt)

    # 支持人数
    backer_count = js['backer_count'] if 'backer_count' in js else 0
    # 支持总额
    backer_money_rew = js['backer_money_rew'] if 'backer_money_rew' in js else 0
    return backer_count,backer_money_rew


def ajax_dialog_user_list(mid, backer_count):
    '''
    请求摩点项目支持者
    :param mid: 摩点项目id
    :param backer_count: 摩点项目支持人数
    :return: 支持者信息
    '''
    pages = backer_count / 20 + 2
    persons = []
    for i in range(1, pages):
        url = 'https://zhongchou.modian.com/realtime/ajax_dialog_user_list?origin_id={}&type=backer_list&page={}&page_size=20'.format(
            mid, i)
        req = requests.get(url, headers=headers)
        txt = req.text
        start = len("window[decodeURIComponent(\'\')](")
        end = len(txt) - 2
        js_txt = txt[start:end]
        js = json.loads(js_txt)

        sel = etree.HTML(js['html'])
        uids = sel.xpath("//div[@class='item_logo']/@data-href")  # 用户id
        unames = sel.xpath("//div[@class='item_cont']/p[1]/text()")  # 用户名
        moneys = sel.xpath("//div[@class='item_cont']/p[2]/text()")  # 软妹币
        for i in range(len(uids)):
            start = uids[i].find('uid=') + 4
            end = uids[i].find('&')
            uid = uids[i][start:end]
            money = float(moneys[i][1:].replace(',', ''))
            person = {'uid': uid, 'uname': unames[i], 'money': money, 'mid': mid}
            persons.append(person)
    return persons


def save_csv(fname, persons):
    '''
    保存到csv文件，一个项目一个
    :param fname: 文件名
    :param persons: 支持者信息
    :return:
    '''
    csvFile = open(fname, "w+")
    try:
        for i in range(len(persons)):
            csvFile.write(persons[i]['money'])  # 保存软妹币
            csvFile.write('\n')
    finally:
        csvFile.close()

    # 查看不重复人数
    # cat m*.csv | sort| uniq | wc -l


def save_postgres(persons):
    '''
    保存到postgres数据库
    :param persons: 支持者信息
    :return:
    '''
    pg_db = 'cosmo'
    pg_host = '127.0.0.1'
    pg_port = '5432'
    pg_name = 'postgres'
    pg_pwd = 'postgres'
    conn = psycopg2.connect(database=pg_db, user=pg_name, password=pg_pwd, host=pg_host, port=pg_port)
    cur = conn.cursor()
    for p in persons:
        sql = "insert into tb_person(mid,uid,uname,money) values(%s,%s,'%s',%s)" % (
            p['mid'], p['uid'], p['uname'], p['money'])
        cur.execute(sql)
    conn.commit()
    conn.close()


# TODO 查看发起过的  'https://me.modian.com/ajax/create_pro_list'


if __name__ == '__main__':
    mids = [
        51808,  # 网宣百猫
    ]

    for mid in mids:
        print(mid)
        backer_count, backer_money_rew = get_simple_product(mid)
        print("人数{}".format(backer_count))
        persons = ajax_dialog_user_list(mid, backer_count)
        # 保存到postgres数据库
        save_postgres(persons)
        # 保存到csv文件
        # fname = './m{}.csv'.format(mid)
        # save_csv(fname, persons)
        # sleep(1)
