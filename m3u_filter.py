import requests
import re
import json
import argparse
import configparser

from netops.utils.email import send_email

def download_file(url, filename):
    r = requests.get(url, allow_redirects=True)

    open(filename, 'wb').write(r.content)
    return

def descr_parse(descr):
    new_descr = {}
    c = 0
    for entry in descr:
        if '=' in entry:
            parsed_entry = entry.replace('=','').replace(' ', '')
            new_descr[parsed_entry] = descr[c+1]
        c+=1
    return new_descr

def channels_parser(filename, new_channels):
    channels={}
    with open(filename) as f:
        for line in f.readlines():
            if 'EXTM3U' in line:
                new_channels.append(line)
            elif 'EXTINF' in line:
                # Parse das entradas pelas descricoes
                entry = line
                channels[entry] = {'descr': None, 'url': None}
                descr = descr_parse(re.split('\"*\"', line.split('#EXTINF:-1 ')[1]))
                channels[entry]['descr'] = descr
            else:
                channels[entry]['url'] = line
    return channels, new_channels

def channels_categoryze(channels):
    # Filter channels per group
    group_titles=[]
    channels_per_group = {}
    for key in channels:
        if not channels[key]['descr']['group-title'] in group_titles:
            group_titles.append(channels[key]['descr']['group-title'])
            channels_per_group[channels[key]['descr']['group-title']] = {}
        channels_per_group[channels[key]['descr']['group-title']][key] = channels[key]

    #print(json.dumps(channels_per_group, indent=4))
    return channels_per_group

def channels_filter(channels_per_group, chosen_groups):
    # Dict of chosen channels based on chosen groups
    chosen_channels = {}
    for group in channels_per_group:
        if group in chosen_groups:
            for channel_key in channels_per_group[group]:
                chosen_channels[channel_key] = channels_per_group[group][channel_key]

    #print(json.dumps(chosen_channels, indent=4))
    return chosen_channels

def dict_to_list_channels(chosen_channels, new_channels):
    #Convert chosen channels dict to list
    for channel_key in chosen_channels:
        new_channels.append(channel_key)
        new_channels.append(chosen_channels[channel_key]['url'])
    return new_channels

def wr_list_to_file(filename_filtered, list):
    # Opening a file
    f = open(filename_filtered, 'w')
    # Writing multiple strings at a time
    f.writelines(list)
    # Closing file
    f.close()
    return

def s_email(type, s_addr, s_pass, r_list):
    if type == 'negative':
        subject = '[IPTV] M3U List Update FAILED'
        message = 'M3U list update FAILED.'
    elif type == 'positive':
        subject = '[IPTV] M3U List Update was SUCCESSFULl'
        message = 'M3U list update SUCCESS.'
    send_email(s_addr, s_pass, r_list, subject, message)
    return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=True)
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read_file(open(args.config, 'r'))
    url = config.get('SETUP', 'URL')
    filename = config.get('SETUP', 'DOWNLOAD_FILE')
    filename_filtered = config.get('SETUP', 'FILTERED_FILE')

    chosen_groups_config = config.get('SETUP', 'CHOSEN_GROUPS')
    chosen_groups = chosen_groups_config.replace('[', '').replace(']','')
    chosen_groups = chosen_groups.split(', ')

    s_addr = config.get('SETUP', 'SENDER_ADDRESS')
    s_pass = config.get('SETUP', 'SENDER_PASS')
    r_list_config = config.get('SETUP', 'RECEIVERS_LIST')
    r_list = r_list_config.replace('[', '').replace(']','')
    r_list = r_list.split(', ')

    new_channels = []
    try:
        download_file(url,filename)
        channels, new_channels = channels_parser(filename, new_channels)
        channels_per_group = channels_categoryze(channels)
        chosen_channels = channels_filter(channels_per_group, chosen_groups)
        new_channels = dict_to_list_channels(chosen_channels, new_channels)
        wr_list_to_file(filename_filtered,new_channels)
        s_email('positive', s_addr, s_pass, r_list)
    except Exception:
        s_email('negative', s_addr, s_pass, r_list)

if __name__ == "__main__":
    main()
