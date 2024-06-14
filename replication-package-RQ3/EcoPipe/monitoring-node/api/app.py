from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import db 
import helper
from urllib.parse import urlparse
#import time

app = Flask(__name__)

load_dotenv('../.env')

for key, value in os.environ.items():
    app.config[key] = value

@app.route('/webhook', methods=['POST'])
def gitlab_webhook():
    data = request.json
    gitlab_event = request.headers.get('X-GitLab-Event')
    gitlab_token = request.headers.get('X-GitLab-Token')

    # Verify token
    if gitlab_token != app.config['GITLAB_TOKEN']:
        return jsonify({'message': 'Unauthorized'}), 401

    # Get DB cursor
    connection = db.get_connection()
    cursor = connection.cursor()

    # Verify event
    if gitlab_event == 'Pipeline Hook':
        project = data['project']
        user = data['user']
        host = urlparse(project['web_url']).hostname
        pipeline = helper.get_pipeline(host, data)

        if pipeline['status'] == 'success':
            db.create_host_if_not_exists(cursor, host)
            db.create_project_if_not_exists(cursor, project, host)
            db.create_user_if_not_exists(cursor, user, host)
            db.create_pipeline_if_not_exists(cursor, pipeline, host)

            stages = helper.get_jobs_by_stage(data)
            
            for stage_name, jobs in stages.items():
                stage_started_at = min(job['started_at'] for job in jobs)
                stage_finished_at = max(job['finished_at'] for job in jobs)

                stage = {
                    'name': stage_name,
                    'pipeline_id': pipeline['id'],
                    'started_at': stage_started_at,
                    'finished_at': stage_finished_at,
                    'consumption': helper.get_stage_consumption(host, stage_started_at, stage_finished_at)
                }

                db.create_pipeline_stage(cursor, stage, host)

                for job in jobs:
                    job['stage'] = stage_name
                    job['pipeline_id'] = pipeline['id']

                    db.create_pipeline_job(cursor, job, host)
        
            for date, consumption in helper.get_pipeline_consumption_rate(host, pipeline).items():
                db.log_pipeline_consumption(cursor, pipeline['id'], host, consumption, date)

    db.commit_and_close(connection)

    """
    end_time = time.time()

    if pipeline['status'] == 'success':
        start_time = pipeline['finished_at'].timestamp()

        with open('execution-time/data.csv', 'a') as file:
            file.write(f'{host},{start_time},{end_time}\n')
    """
    return jsonify({'message': 'Received'}), 200

if __name__ == '__main__':
    app.run(debug=True, host=app.config['API_HOST'], port=app.config['API_PORT'])