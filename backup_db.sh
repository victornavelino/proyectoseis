#!/bin/sh
##########################################
## Carniceria Virgen del valle Backup databases: vvalle
##########################################
# La contraseña de PostgreSQL NUNCA debe hardcodearse acá: este archivo está
# versionado en git. Exportá PGPASSWORD en el entorno donde corra este script
# (por ejemplo, en el crontab del usuario que lo ejecuta, o en un archivo
# .env local fuera del repo que se source antes de invocarlo) antes de
# llamarlo.
: "${PGPASSWORD:?Debes exportar PGPASSWORD con la contraseña de PostgreSQL antes de ejecutar este script}"
export PGPASSWORD

# Dump DBs
db="vvalle"
date=`date +"%Y%m%d_%H%M%N"`
filename="/home/vvalle/proyectovvalle/backups_db/${db}_${date}.sql"
docker exec -i  $(docker container ls  | grep 'carniceriavv_db' | awk '{print $1}') pg_dump -U postgres -h localhost -p 5432 -F p -b $db > $filename
gzip $filename
find /home/vvalle/proyectovvalle/backups_db/ -type f -mtime +30 -name '*.sql.gz' -execdir rm -- '{}' \;
exit 0