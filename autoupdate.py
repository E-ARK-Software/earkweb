import subprocess32
from config.configuration import solr_field_list, solr_copy_fields, solr_config_changes
import time

""" This script performs an update of EARKweb. This includes:
* db migrations
* updates to Solr schema
* updating existing/adding new Celery tasks
"""

# colour codes
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

# # requirements.txt: install new requirements
# print '\033[95m' + '----------------\nNow updating from requirements.txt.\n----------------' + '\033[0m'
# req_update_args = ['pip', 'install', '-r', 'requirements.txt']
# update_process = subprocess32.Popen(req_update_args)
# update_out, update_err = update_process.communicate()
# if update_err is not None:
#     print WARNING + 'There have been errors when updating from requirements.txt:\n' + '\033[0m'
#     print update_err

# migrations - prepare
print HEADER + '----------------\nNow preparing database migrations.\n----------------' + ENDC
migrations_update_args = ['python', 'manage.py', 'makemigrations']
migrations_process = subprocess32.Popen(migrations_update_args)
migrations_out, migrations_err = migrations_process.communicate()
if migrations_err is not None:
    print WARNING + 'There have been errors when performing migrations:\n' + ENDC
    print migrations_err

# migrations - apply
print HEADER + '----------------\nNow applying database migrations.\n----------------' + ENDC
migrations_update_args = ['python', 'manage.py', 'migrate']
migrations_process = subprocess32.Popen(migrations_update_args)
migrations_out, migrations_err = migrations_process.communicate()
if migrations_err is not None:
    print WARNING + 'There have been errors when performing migrations:\n' + ENDC
    print migrations_err

# scan for new/updated Celery tasks
print HEADER + '----------------\nNow scanning for new/updated Celery tasks.\n----------------' + ENDC
taskscan_args = ['python', 'workers/scantasks.py']
taskscan_process = subprocess32.Popen(taskscan_args)
taskscan_out, taskscan_err = taskscan_process.communicate()
if taskscan_err is not None:
    print WARNING + + 'There have been errors when updating Celery tasks:\n' + ENDC
    print taskscan_err

# Solr: create new fields
print HEADER + '----------------\nNow adding new Solr fields.\n----------------' + ENDC
for field in solr_field_list:
    print OKBLUE + '## Adding new field: %s ##' % field['name'] + ENDC
    # simple field with name, type, stored parameter
    solr_fields_args = ['curl', '-X', 'POST', '-H', '\'Content-type:application/json\'',
                        '--data-binary', '{"add-field": {"name": "%s", "type": "%s", "stored": "%s"}}' % (field['name'], field['type'], field['stored']),
                        'http://localhost:8983/solr/earkstorage/schema']
    try:
        # check if 'indexed' is set (additional to parameters above)
        if field['indexed']:
            solr_fields_args = ['curl', '-X', 'POST', '-H', '\'Content-type:application/json\'',
                                '--data-binary', '{"add-field": {"name": "%s", "type": "%s", "stored": "%s", "indexed": "%s"}}' % (field['name'], field['type'], field['stored'], field['indexed']), 'http://localhost:8983/solr/earkstorage/schema']
    except KeyError:
        # expected behaviour if 'indexed' is not set
        pass

    solr_fields_process = subprocess32.Popen(solr_fields_args)
    solr_fields_out, solr_fields_err = solr_fields_process.communicate()
    if solr_fields_err is not None:
        print WARNING + 'There have been errors when updating Solr fields:\n' + ENDC
        print solr_fields_err

time.sleep(2.5)

for field in solr_copy_fields:
    print OKBLUE + '## Adding new copy-field: from %s to %s ##' % (field['source'], field['dest']) + ENDC
    solr_fields_args = ['curl', '-X', 'POST', '-H', '\'Content-type:application/json\'',
                        '--data-binary', '{"add-copy-field": {"source": "%s", "dest": "%s"}}' % (field['source'], field['dest']),
                        'http://localhost:8983/solr/earkstorage/schema']

    solr_fields_process = subprocess32.Popen(solr_fields_args)
    solr_fields_out, solr_fields_err = solr_fields_process.communicate()
    if solr_fields_err is not None:
        print WARNING + 'There have been errors when updating Solr fields:\n' + ENDC
        print solr_fields_err

print HEADER + '----------------\nNow editing the Solr config.\n----------------' + ENDC
for change in solr_config_changes:
    print OKBLUE + '## Editing class: %s ##' % change['class'] + ENDC
    solr_config_args = ['curl', 'http://localhost:8983/solr/earkstorage/config', '-H', '\'Content-type:application/json\'',
                        '-d', '{"%s":{"name":"%s", "class":"%s", "defaults": %s}}' %
                        (change['type'], change['path'], change['class'], change['fields'])]
    solr_change_process = subprocess32.Popen(solr_config_args)
    solr_change_out, solr_change_err = solr_change_process.communicate()
    if solr_change_err is not None:
        print WARNING + 'There have been errors when updating the Solr config file:\n' + ENDC
        print solr_change_err
