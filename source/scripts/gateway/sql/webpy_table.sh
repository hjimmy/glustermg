mysql -u gluster -pneokylin123  -D webpy < /opt/glustermg/2.4/glustermg/scripts/gateway/sql/0-version.sql
mysql -u gluster -pneokylin123  -D webpy < /opt/glustermg/2.4/glustermg/scripts/gateway/sql/1-security-schema.sql
mysql -u gluster -pneokylin123  -D webpy < /opt/glustermg/2.4/glustermg/scripts/gateway/sql/2-users-authorities-groups.sql
mysql -u gluster -pneokylin123  -D webpy < /opt/glustermg/2.4/glustermg/scripts/gateway/sql/3-cluster-servers.sql

