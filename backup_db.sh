#!/bin/sh
##########################################
## Carniceria Virgen del valle Backup databases: vvalle
##########################################
# Dump DBs
db="vvalle"
date=`date +"%Y%m%d_%H%M%N"`
filename="/home/vvalle/proyectovvalle/backups_db/${db}_${date}.sql"
export PGPASSWORD="vallE.852"
docker exec -i  $(docker container ls  | grep 'carniceriavv_db' | awk '{print $1}') pg_dump -U postgres -h localhost -p 5432 -F p -b $db > $filename
gzip $filename
find /home/vvalle/proyectovvalle/backups_db/ -type f -mtime +30 -name '*.sql.gz' -execdir rm -- '{}' \;
exit 0