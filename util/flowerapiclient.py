#!/usr/bin/env python
# coding=UTF-8
import requests
import json

import datetime

from config.configuration import flower_path, flower_port, flower_host, verify_certificate, \
    flower_host


def get_task_info(task_id):
    flower_request_url = 'http://%s:%s%sapi/tasks' % (flower_host, flower_port, flower_path)
    print(flower_request_url)
    response = requests.get(flower_request_url,
                            verify=verify_certificate, headers={'Connection': 'close'})
    tasks_json = json.loads(response.text)
    print(tasks_json)
    task_json = tasks_json[task_id]
    task_name = task_json['name']
    task_runtime = None
    if 'runtime' in task_json and isinstance(task_json['runtime'], int):
        task_runtime = round(task_json['runtime'], 2)
    process_id = None
    if 'args' in task_json:

        from ast import literal_eval
        tpl = literal_eval(task_json["args"])
        if isinstance(tpl[0], dict):
            js = tpl[0]
        else:
            js = json.loads(tpl[0])
        process_id = js["process_id"]
    task_received = datetime.datetime.fromtimestamp(int(task_json['received'])).strftime('%Y-%m-%d %H:%M:%S')

    task_info = {
        "name": task_name,
        "received": task_received,
    }
    if task_runtime:
        task_info["runtime"] = task_runtime
    if process_id:
        task_info["process_id"] = process_id
    return task_info


def get_task_list(task_id, exclude_tasks:list=None):
    flower_request_url = 'http://%s:%s%sapi/tasks' % (flower_host, flower_port, flower_path)
    response = requests.get(flower_request_url, verify=verify_certificate, headers={'Connection': 'close'})
    tasks_json = json.loads(response.text)
    task_ids = []
    if task_id in tasks_json:
        def find_tasks(t_id):
            t_info = tasks_json[t_id]
            if 'children' in t_info:
                for child_task in t_info['children']:
                    if exclude_tasks and tasks_json[child_task]['name'] not in exclude_tasks:
                        task_ids.append(child_task)
                    find_tasks(child_task)
        find_tasks(task_id)
    else:
        raise ValueError("Task not found: %s" % task_id)
    return [tasks_json[tid] for tid in task_ids]


if __name__ == '__main__':
    tl = get_task_list('b6791fd7-d7df-41c3-916b-ec046fe15a59', ['file_migration'])
    print(len(tl))
    for t in tl:
        print(t)
