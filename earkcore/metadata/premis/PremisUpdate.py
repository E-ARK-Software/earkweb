__author__ = 'jan'

import os
from tasklogger import TaskLogger as tl

'''
Updates PREMIS file.
'''

def add_event(task, outcome, identifier_value,  linking_agent, package_premis_file, ip_work_dir):
#def add_event(task_info):
    '''
    Add an event to the PREMIS file and update it afterwards.
    '''
    #task = task_info[0]
    #outcome = task_info[1]
    #identifier_value = task_info[2]
    #linking_agent = task_info[3]
    #package_premis_file = task_info[4]
    #ip_work_dir = task_info[5]

    package_premis_file.add_event(task, outcome, identifier_value, linking_agent)
    path_premis = os.path.join(ip_work_dir, "metadata/PREMIS.xml")
    with open(path_premis, 'w') as output_file:
        output_file.write(package_premis_file.to_string())
    tl.addinfo('PREMIS file updated: %s' % path_premis)