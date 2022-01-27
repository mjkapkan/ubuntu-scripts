#!/usr/bin/python3

import os
import uuid
import subprocess
import sys

NETWORK_CONF_DIR = '/etc/NetworkManager/system-connections/'

def run_cmd(cmd):
    process = subprocess.Popen(cmd.split(' '),
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()

    str_output = []
    for paragraph in stdout.decode("utf-8").split('\\n'):
        for line in paragraph.split('\n'):
            str_output.append(line)
            
                          
    return str_output

def get_mac_list(cmd_output,name):
    bssid_list = []
    for line in cmd_output:
        data = line.replace('\:','***').split(':')
        ssid = data[0]
        bssid = ''
        if len(data) > 1:
            bssid = data[1].replace('***',':')
        if ssid == name:
            bssid_list.append(bssid)
    return bssid_list

def find_wifi_connection (name,conf_type):
    available_conn = os.listdir(NETWORK_CONF_DIR)
    reverse_types = {
        'blacklist': 'whitelist',
        'whitelist': 'blacklist'
        }
    for conf_file in available_conn:
        BSSID = conf_file.split('.nmconnection')[0]
        if BSSID == name or name + '_'+conf_type+'ed_' in BSSID or name + '_'+reverse_types[conf_type]+'ed_' in BSSID:
            return NETWORK_CONF_DIR + conf_file
    return

def remove_origin_connection (name):
    available_conn = os.listdir(NETWORK_CONF_DIR)
    for conf_file in available_conn:
        BSSID = conf_file.split('.nmconnection')[0]
        if BSSID == name:
            print('removing original connection...')
            wifi_conf_file = NETWORK_CONF_DIR + conf_file
            os.remove(wifi_conf_file)
    return

def scan_wifi_connection (name,mac_address,conf_type):
    available_conn = os.listdir(NETWORK_CONF_DIR)
    reverse_types = {
        'blacklist': 'whitelist',
        'whitelist': 'blacklist'
        }
    for conf_file in available_conn:
        BSSID = conf_file.split('.nmconnection')[0]
        if name + '_'+reverse_types[conf_type]+'ed_' in BSSID:
            wifi_conf_file = NETWORK_CONF_DIR + conf_file
            remove = False
            with open(wifi_conf_file, 'r', encoding='UTF-8') as conn_params:
                for line in conn_params:
                    if 'BSSID='+mac_address in line.upper():
                        remove = True
            if remove:
                print('removing conficting file: ' + conf_file)
                os.remove(wifi_conf_file)
    for conf_file in available_conn:
        BSSID = conf_file.split('.nmconnection')[0]
        if BSSID == name or name + '_'+conf_type+'ed_' in BSSID:
            wifi_conf_file = NETWORK_CONF_DIR + conf_file
            with open(wifi_conf_file, 'r', encoding='UTF-8') as conn_params:
                for line in conn_params:
                    if 'BSSID='+mac_address in line.upper():
                        print('No changes made. ' + mac_address + ' already ' + conf_type + 'ed in ' + conf_file)
                        return True
    return False

def new_conf_name (name,conf_type):
    available_conn = os.listdir(NETWORK_CONF_DIR)
    bad_num = 0
    while True:
        new_name = name + '_'+conf_type+'ed_' + str(bad_num)
        if new_name  + '.nmconnection' in available_conn:
            bad_num += 1
        else:
            return new_name

def change_conf_mac (line,mac_address,add_bssid):
    if add_bssid:
        if '[wifi]' in line:
            new_line = 'bssid=' + mac_address + '\n'
            return line + new_line

    else:
        param = line.strip().split('=')
        param_name = param[0]
        if param_name == 'bssid':
            param_value = param[1]
            if param_value != mac_address:
                param_value = mac_address
                line = param_name + '=' + param_value + '\n'
                return line
    return False

def change_conf_id (line,name,new_name):
    param = line.strip().split('=')
    param_name = param[0]
    if param_name == 'id':
        param_value = new_name
        line = param_name + '=' + param_value + '\n'
        return line
    return False

def change_conf_uuid (line):
    param = line.strip().split('=')
    param_name = param[0]
    if param_name == 'uuid':
        param_value = str(uuid.uuid1())
        line = param_name + '=' + param_value + '\n'
        return line
    return False

def change_autoconnect (line,value):
    if 'type=wifi' in line:
        new_line = 'autoconnect='+value+'\n'
        return line + new_line
    return False

def remove_conf (line):
    triggers = ['seen-bssids=','autoconnect=']
    for string in triggers:
        if string in line:
            return True
    return False

def blacklist_bssid (name,mac_address):
    conf_type = 'blacklist'
    if scan_wifi_connection(name,mac_address,conf_type):
        return False
    wifi_conf_file = find_wifi_connection(name,conf_type)
    if wifi_conf_file == None:
        print('No exisitng wifi config found for this name!')
        return False
    new_conf_file_data = []
    new_conf_id = new_conf_name(name,conf_type)
    new_conf_file_name = NETWORK_CONF_DIR + new_conf_id + '.nmconnection'
    changes_needed = False
    add_bssid = True
    with open(wifi_conf_file, 'r', encoding='UTF-8') as conn_params:
        for line in conn_params:
            if 'bssid=' in line.lower():
                add_bssid = False
        conn_params.seek(0)
        for line in conn_params:
            if remove_conf(line):
                continue
            changed_line = line
            for change in [
                change_autoconnect(line,'false'),
                change_conf_mac(line,mac_address,add_bssid),
                change_conf_id(line,name,new_conf_id),
                change_conf_uuid(line)
                ]:
                if change:
                    changed_line = change
                    break
            new_conf_file_data.append(changed_line)
            if line.strip() != changed_line.strip():
                if 'uuid=' not in line and 'type=wifi' not in line:
                    changes_needed = True
    if changes_needed:
        with open(new_conf_file_name, 'w', encoding='UTF-8') as conn_params:
            print('writing params..')
            for param_line in new_conf_file_data:
                conn_params.write(param_line)
            print('New '+conf_type+' for '+mac_address+' added as: ' + new_conf_id)
        os.chmod(new_conf_file_name, 0o600)
        return True
    else:
        print('No changes made. ' + mac_address + ' already in ' + conf_type)
        return False


def whitelist_bssid (name,mac_address):
    conf_type = 'whitelist'
    if scan_wifi_connection(name,mac_address,conf_type):
        return False
    wifi_conf_file = find_wifi_connection(name,conf_type)
    if wifi_conf_file == None:
        print('No exisitng wifi config found for this name!')
        return False
    new_conf_file_data = []
    new_conf_id = new_conf_name(name,conf_type)
    new_conf_file_name = NETWORK_CONF_DIR + new_conf_id + '.nmconnection'
    changes_needed = False
    add_bssid = True
    with open(wifi_conf_file, 'r', encoding='UTF-8') as conn_params:
        for line in conn_params:
            if 'bssid=' in line.lower():
                add_bssid = False
        conn_params.seek(0)
        for line in conn_params:
            if remove_conf(line):
                continue
            changed_line = line
            for change in [
                change_autoconnect(line,'true'),
                change_conf_mac(line,mac_address,add_bssid),
                change_conf_id(line,name,new_conf_id),
                change_conf_uuid(line)
                ]:
                if change:
                    changed_line = change
                    break
            new_conf_file_data.append(changed_line)
            if line.strip() != changed_line.strip():
                if 'uuid=' not in line and 'type=wifi' not in line:
                    changes_needed = True
    if changes_needed:
        with open(new_conf_file_name, 'w', encoding='UTF-8') as conn_params:
            for param_line in new_conf_file_data:
                conn_params.write(param_line)
            print('New '+conf_type+' for '+mac_address+' added as: ' + new_conf_id)
        os.chmod(new_conf_file_name, 0o600)
        return True
    else:
        print('No changes made. ' + mac_address + ' already in ' + conf_type)
        return False


def blacklist_wifi_connections (wifi_name,macs_to_block):
    mac_blacklist = macs_to_block.strip().split(',')
    mac_list = get_mac_list(run_cmd('nmcli -t -f ssid,bssid dev wifi'),'PVcase')

    change_list = []

    for mac in mac_blacklist:
        if len(mac.split(':')) > 5:
            change_list.append(blacklist_bssid(wifi_name,mac))

    for mac in mac_list:
        if mac not in mac_blacklist:
            change_list.append(whitelist_bssid(wifi_name,mac))

    if True in change_list:
        remove_origin_connection(wifi_name)
        print('Restarting network manager...')
        subprocess.Popen('service network-manager restart',shell=True)

def read_config (conf_file):
    try:
        with open(conf_file, 'r', encoding ='UTF-8') as conf:
            for line in conf:
                if line.strip()[0] != '#':
                    params = line.split(' ')
                    SSID = params[0]
                    BSSID = params[1]
                    return SSID, BSSID
    except FileNotFoundError as err:
        print(str(err))
    return False, False
    

try:
    wifi_name = sys.argv[1]
    if wifi_name[:6] == '--conf':
        conf_file = sys.argv[2]
        wifi_name, mac_blocklist_str = read_config (conf_file)
        if not wifi_name:
            print('Corrupt or mising config file!')
            sys.exit()
    else:
        mac_blocklist_str = sys.argv[2]
    
    blacklist_wifi_connections(wifi_name,mac_blocklist_str)
except IndexError:
    print('Usage: [Wifi Name (SSID)] [MAC Address (BSSID) List (comma delimited)]')
    print('Or specify text file with the same format: --conf [config file].\nConfig will be read from first uncommented line.')
except PermissionError:
    print('Network manager config access requires admin privileges (use sudo :>)')

## Example:
# blacklist_wifi_connections('SampleWifiNAme','34:20:E3:02:E6:B8,34:20:E3:02:E5:48,')
