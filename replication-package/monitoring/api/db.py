import psycopg2
from flask import current_app

def get_connection():
    return psycopg2.connect(
        database = current_app.config['DB_NAME'], 
        user = current_app.config['DB_USER'], 
        host= current_app.config['DB_HOST'],
        password = current_app.config['DB_PASS'],
        port = current_app.config['DB_PORT']
    )

def create_host_if_not_exists(cursor, host):
    cursor.execute("INSERT INTO hosts (host) VALUES (%s) ON CONFLICT DO NOTHING;", (host,))

def create_project_if_not_exists(cursor, project, host):
    cursor.execute("INSERT INTO projects (id, name, host) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;", (project['id'], project['name'], host))

def create_user_if_not_exists(cursor, user, host):
    cursor.execute("INSERT INTO users (id, username, name, host) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;", (user['id'], user['username'], user['name'], host))

def create_pipeline_if_not_exists(cursor, pipeline, host):
    cursor.execute("INSERT INTO pipelines (id, host, project_id, project_name, commit_id, user_id, username, status, started_at, finished_at, consumption) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id, host) DO UPDATE SET finished_at = excluded.finished_at;", (pipeline['id'], host, pipeline['project_id'], pipeline['project_name'], pipeline['commit_id'], pipeline['user_id'], pipeline['username'], pipeline['status'], pipeline['started_at'], pipeline['finished_at'], pipeline['consumption']))

def create_pipeline_stage(cursor, stage, host):
    cursor.execute("INSERT INTO stages (name, pipeline_id, host, started_at, finished_at, consumption) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;", (stage['name'], stage['pipeline_id'], host, stage['started_at'], stage['finished_at'], stage['consumption']))

def create_pipeline_job(cursor, job, host):
    cursor.execute("INSERT INTO jobs (id, pipeline_id, host, name, stage, status, started_at, finished_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;", (job['id'], job['pipeline_id'], host, job['name'], job['stage'], job['status'], job['started_at'], job['finished_at']))

def log_pipeline_consumption(cursor, pipeline_id, host, consumption, date):
    cursor.execute("INSERT INTO consumption_rate (pipeline_id, host, consumption, \"time\") VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;", (pipeline_id, host, consumption, date))

def commit_and_close(connection):
    connection.commit()
    connection.close()