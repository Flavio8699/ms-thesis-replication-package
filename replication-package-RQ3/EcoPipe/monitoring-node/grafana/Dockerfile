FROM grafana/grafana

COPY /datasource.yml /etc/grafana/provisioning/datasources/
COPY /dashboards.yml /etc/grafana/provisioning/dashboards/
RUN /usr/share/grafana/bin/grafana-cli plugins install volkovlabs-echarts-panel
COPY /dashboard.json /var/lib/grafana/dashboards/