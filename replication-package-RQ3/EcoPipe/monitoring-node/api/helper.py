import prometheus
from dateutil import parser
from datetime import timedelta

def get_pipeline(host, pipeline):
    finished_at = pipeline['object_attributes']['finished_at']
    queued_duration = timedelta(seconds=pipeline['object_attributes']['queued_duration']) if pipeline['object_attributes']['queued_duration'] is not None else timedelta(seconds=0)
    
    return {
        'id':               pipeline['object_attributes']['id'],
        'project_id':       pipeline['project']['id'],
        'project_name':     pipeline['project']['name'],
        'commit_id':        pipeline['commit']['id'],
        'user_id':          pipeline['user']['id'],
        'username':         pipeline['user']['username'],
        'status':           pipeline['object_attributes']['status'],
        'started_at':       parser.parse(pipeline['object_attributes']['created_at']) + queued_duration,
        'finished_at':      parser.parse(finished_at) if finished_at else None,
        'consumption':      prometheus.get_consumption_microjoules(host, parser.parse(finished_at), pipeline['object_attributes']['duration']) if finished_at else 0
    }

def get_job(job):
    return {
        'id':           job['id'],
        'name':         job['name'],
        'started_at':   parser.parse(job['started_at']),
        'finished_at':  parser.parse(job['finished_at']),
        'status':       job['status']
    }

def get_jobs_by_stage(data):
    stages = {}

    for job in data['builds']:
        stage = job['stage']

        if stage not in stages:
            stages[stage] = []

        stages[stage].append(get_job(job))
    
    return stages

def get_dates(end, interval, duration):
    dates = []
    end_date = end

    for _ in range(duration // interval):
        end_date -= timedelta(seconds=interval)
        dates.append(end_date)

    return list(reversed(dates))

def get_pipeline_consumption_rate(host, pipeline):
    pipeline_duration = int((pipeline['finished_at'] - pipeline['started_at']).total_seconds())
    dates = get_dates(pipeline['finished_at'], interval=5, duration=pipeline_duration)

    data = {}

    for date in dates:
        consumption = prometheus.get_consumption_rate_microjoules(host, date)
        data[date] = consumption

    return data

def get_stage_consumption(host, start, finish):
    stage_duration = int((finish - start).total_seconds())
    return prometheus.get_consumption_microjoules(host, finish, stage_duration)