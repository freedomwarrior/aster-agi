#!/usr/bin/python3
import sys
import pymysql.cursors
import subprocess
from datetime import datetime


env = {}
tests = 0
fping = '/usr/bin/fping'
logPath = '/usr/share/asterisk/agi-bin/checker.log'

# env['agi_callerid'] - client phone number
dt = datetime.now()

def mysql_fetch_ub(queru):
    connection = pymysql.connect(host='',
                                 user='',
                                 password='',
                                 db='stg',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            cursor.execute(queru)
            result = cursor.fetchall()

    finally:
        connection.commit()
        connection.close()

    return result

def parse_stdin():
    while 1:
        line = sys.stdin.readline().strip()
        if line == '':
            break
        key, data = line.split(':')
        if key[:4] != 'agi_':
            #skip input that doesn't begin with agi_
            sys.stderr.write("Did not work!\n")
            sys.stderr.flush()
            continue
        key = key.strip()
        data = data.strip()
        if key != '':
            env[key] = data
    if len(env['agi_callerid']) > 3:
        return env['agi_callerid']
    else:
        return env['agi_calleridname'].replace('++38', '').replace('+38', '')



def check_switch(ips):
    result = 0
    for ip in ips:
        process = subprocess.Popen([fping, ip],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        stdout, stderr
        res = stdout.decode('utf-8')
        if 'unreachable' in res:
            result = 1
    return result



def get_client_data(mobile):
    """
    :param mobile: Client mobile phone
    :return: return list of IP`s
    """
    sw_list = []
    query = 'select login from phones where mobile like \'%{0}%\' or phone like \'%{0}%\''.format(mobile)
    data = mysql_fetch_ub(query)
    if data:
        for login in data:
            query = 'select switches.ip from switches inner join pononu on switches.id = pononu.oltid and pononu.login=\'{}\''.format(login['login'])
            data = mysql_fetch_ub(query)
            if data:
                for sw in data:
                    sw_list.append(sw['ip'])
            query = 'select switches.ip from switches inner join switchportassign on switches.id = switchportassign.switchid and switchportassign.login=\'{}\''.format(
                login['login'])
            data = mysql_fetch_ub(query)
            if data:
                for sw in data:
                    sw_list.append(sw['ip'])
    return sw_list



def main():
    result = 0
    client_number = parse_stdin()
    client_switches = get_client_data(client_number)
    if client_switches:
        check_data = check_switch(client_switches)
        if check_data == 1:
            with open(logPath, 'a+') as f:
                logWrite = dt.strftime("[%m-%d-%y %H:%M:%S] ") + client_number
                f.write(logWrite + '\n')
            result = 1
    sys.stdout.write("SET VARIABLE ScriptResult {}\n".format(result))


if __name__ == '__main__':
    main()