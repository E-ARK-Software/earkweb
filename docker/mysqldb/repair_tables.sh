#!/usr/bin/env bash
DATATABLES=( auth_group auth_group_permissions auth_permission auth_user_groups auth_user auth_user_user_permissions celery_taskmeta celery_tasksetmeta \
            config_path django_admin_log django_content_type django_migrations django_session djcelery_crontabschedule djcelery_crontabschedule djcelery_intervalschedule \
            djcelery_periodictask djcelery_periodictasks djcelery_taskstate djcelery_workerstate earkcore_informationpackage search_aip search_dip search_inclusion \
            sip2aip_mymodel wirings workflow_workflowmodules)
for DATATABLE in "${DATATABLES[@]}"
do
    myisamchk -r -q "/var/lib/mysql/earkdb/$DATATABLE"
done