CREATE TABLE hosts
  (
     host   VARCHAR(255) UNIQUE NOT NULL,
     PRIMARY KEY (host)
  ); 

CREATE TABLE projects
  (
     id        INTEGER NOT NULL,
     name      VARCHAR(255) NOT NULL,
     host      VARCHAR(255) NOT NULL,
     FOREIGN KEY (host) REFERENCES hosts (host) ON DELETE CASCADE,
     PRIMARY KEY (id, name, host)
  );

CREATE TABLE users
  (
     id        INTEGER NOT NULL,
     username  VARCHAR(255) NOT NULL,
     name      VARCHAR(255) NOT NULL,
     host      VARCHAR(255) NOT NULL,
     FOREIGN KEY (host) REFERENCES hosts (host) ON DELETE CASCADE,
     PRIMARY KEY (id, username, host)
  ); 
  
CREATE TABLE pipelines
  (
     id           INTEGER NOT NULL,
     host         VARCHAR(255) NOT NULL,
     project_id   INTEGER NOT NULL,
     project_name VARCHAR(255) NOT NULL,
     commit_id    VARCHAR(255) NOT NULL,
     user_id      INTEGER NOT NULL,
     username     VARCHAR(255) NOT NULL,
     status       VARCHAR(255) NOT NULL,
     started_at   TIMESTAMP WITH TIME ZONE NOT NULL,
     finished_at  TIMESTAMP WITH TIME ZONE NOT NULL,
     consumption  FLOAT,
     FOREIGN KEY (project_id, project_name, host) REFERENCES projects (id, name, host) ON DELETE CASCADE,
     FOREIGN KEY (user_id, username, host) REFERENCES users (id, username, host) ON DELETE CASCADE,
     PRIMARY KEY (id, host)
  );

CREATE TABLE stages
   (
      name           VARCHAR(255) NOT NULL,
      pipeline_id    INTEGER NOT NULL,
      host           VARCHAR(255) NOT NULL,
      started_at     TIMESTAMP WITH TIME ZONE NOT NULL,
      finished_at    TIMESTAMP WITH TIME ZONE NOT NULL,
      consumption    FLOAT,
      FOREIGN KEY (pipeline_id, host) REFERENCES pipelines (id, host) ON DELETE CASCADE,
      PRIMARY KEY (name, pipeline_id, host)
   );

CREATE TABLE jobs
  (
      id             INTEGER NOT NULL,
      pipeline_id    INTEGER NOT NULL,
      host           VARCHAR(255) NOT NULL,
      name           VARCHAR(255) NOT NULL,
      stage          VARCHAR(255) NOT NULL,
      status         VARCHAR(255) NOT NULL,
      started_at     TIMESTAMP WITH TIME ZONE NOT NULL,
      finished_at    TIMESTAMP WITH TIME ZONE,
      FOREIGN KEY (pipeline_id, host) REFERENCES pipelines (id, host) ON DELETE CASCADE,
      FOREIGN KEY (stage, pipeline_id, host) REFERENCES stages (name, pipeline_id, host) ON DELETE CASCADE,
      PRIMARY KEY (id, host)
  );

CREATE TABLE consumption_rate
   (
      pipeline_id    INTEGER NOT NULL,
      host           VARCHAR(255) NOT NULL,
      consumption    FLOAT NOT NULL,
      time           TIMESTAMP WITH TIME ZONE NOT NULL,
      FOREIGN KEY (pipeline_id, host) REFERENCES pipelines (id, host) ON DELETE CASCADE,
      PRIMARY KEY (pipeline_id, host, time)
   );