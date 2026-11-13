# Plan: migración de la base de datos on-premise → Dokploy

Contexto: el sistema actual corre "on premise" en su versión Django puro (sin el frontend
React nuevo, ver `DECISIONES.md` DEC-009). Este documento es el plan para sacar un backup de esa
base de datos de producción y restaurarlo en el Postgres de Dokploy, cuando se decida cortar el
corte definitivo hacia la infraestructura nueva.

**Estado**: plan preparado, no ejecutado todavía. Actualizar este archivo con la fecha y el
resultado una vez que se corra.

---

## Datos del entorno destino (Dokploy, relevados el 2026-09-01)

- Contenedor Postgres compartido: `postgresqlcompartido-db-4zupfz` (imagen `postgres:18`,
  versión real `18.6`).
- Base de datos de la app: `carniceriavv`, rol/usuario: `carniceriavv` (mismo nombre).
- La app se conecta vía `DATABASE_URL` (env var del servicio `carniceria-vv-service-uhg2lr` en
  Dokploy) — no cambiar el nombre de la base ni del rol sin actualizar esa variable.
- Al momento de escribir esto, la base en Dokploy está vacía / solo tiene lo que dejaron las
  migraciones (`manage.py migrate`, corre automático en cada arranque vía `entrypoint.sh`) — no
  hay datos reales de negocio que preservar ahí. **Confirmar que esto sigue siendo así antes de
  ejecutar el restore** (si para ese momento ya hay ventas/clientes reales cargados en Dokploy,
  este plan de "overwrite" no sirve tal cual — hay que planear un merge en su lugar).

## Origen (on-premise)

Motor: PostgreSQL (confirmado). Faltan al momento de escribir esto: host/puerto, nombre de la
base y usuario concretos de esa instalación — completar antes de ejecutar el paso 1.

---

## Paso 1 — Backup en el on-premise

Lo corre quien tenga acceso a ese servidor (no hay acceso remoto de Claude ahí). Formato
*custom* de `pg_dump` (comprimido, permite `--clean` y restore selectivo, más flexible que un
dump plano):

```bash
pg_dump -Fc \
  -h <host_db_onpremise> \
  -p <puerto, 5432 por defecto> \
  -U <usuario_db> \
  -d <nombre_db> \
  -f carniceriavv_backup.dump
```

## Paso 2 — Subir el dump a la VPS de Dokploy

Directo servidor a servidor (no hace falta pasar por ninguna PC intermedia), con el acceso SSH
propio a la VPS:

```bash
scp -P 5557 carniceriavv_backup.dump root@vps-6304176-x.dattaweb.com:/root/
```

Si el on-premise no tiene salida a internet, alternativa en dos pasos: bajarlo a una PC con
acceso a ambos lados y de ahí hacer el `scp` a la VPS.

## Paso 3 — Restore en Dokploy

Con el archivo ya en `/root/carniceriavv_backup.dump` en la VPS:

1. Parar el contenedor de la app (`carniceria-vv-service-uhg2lr`) para que no escriba nada
   mientras se restaura.
2. Copiar el dump al contenedor de Postgres y restaurar:

   ```bash
   docker cp /root/carniceriavv_backup.dump <container_postgres>:/tmp/backup.dump
   docker exec <container_postgres> pg_restore \
     -U carniceriavv -d carniceriavv \
     --clean --if-exists --no-owner --no-privileges \
     -v /tmp/backup.dump
   ```

   - `--clean --if-exists`: limpia lo que haya antes de recrear todo desde el backup (pisa la
     base actual — ver la advertencia de arriba sobre confirmar que no tiene datos reales).
   - `--no-owner --no-privileges`: evita errores si el rol del on-premise no coincide con
     `carniceriavv` (el rol de Dokploy).
3. Levantar de nuevo el contenedor de la app y verificar (login, algún listado con datos, que
   `manage.py migrate` no reporte nada pendiente — el dump ya debería traer el esquema al día si
   el on-premise corría la misma versión del código o una anterior compatible).

## Pendiente antes de ejecutar

- [ ] Confirmar host/puerto/usuario/nombre de la base on-premise.
- [ ] Confirmar que la base `carniceriavv` en Dokploy sigue sin datos reales (o replantear como
      merge si ya los tiene).
- [ ] Definir una ventana de corte (el sistema on-premise deja de recibir escrituras mientras se
      saca el dump final, para no perder ventas/movimientos hechos después del backup).
- [ ] Backup del estado actual de la base en Dokploy antes de pisarla (aunque sea de prueba), por
      las dudas.
