import streamlit as st
from psycopg import connect, sql, extras

@st.cache_resource(show_spinner="Savienojas ar datu bāzi")
def db_savienojums():
    db = st.secrets["postgres_db"]

    return connect(
        host=db["host"],
        dbname=db["datu_baze"],
        user=db["lietotajs"],
        password=db["parole"],
        port=db["port"]
    )

def vaicat_db(vaicajums, argumenti=(), dabut_vienu=True, rediget_rindu=False):
    savienojums = db_savienojums()

    try:
        with savienojums.cursor() as cur:
            cur.execute("SELECT 1;")
    except:
        st.cache_resource.clear()
        savienojums = db_savienojums()

    vaicajums = sql.SQL(vaicajums)
    try:
        with savienojums.cursor(cursor_factory=extras.DictCursor) as cursor:
            cursor.execute(vaicajums, argumenti)

            if rediget_rindu:
                savienojums.commit()
            else:
                return cursor.fetchone() if dabut_vienu else cursor.fetchall()
    except Exception as e:
        st.error(f"Kļūda datu bāzes vaicājumā: {e}")

def vai_pilnvarots_epasts():
    vaicajums = "SELECT * FROM autorizeti_epasti WHERE epasts = %s"

    rezultats = vaicat_db(vaicajums, (st.user.email,))

    return rezultats is not None

### Pieprasijuma funkcijas
def dabut_lietotaju_pec_epasta():
    vaicajums = "SELECT * FROM lietotaji WHERE epasts = %s"

    return vaicat_db(vaicajums, (st.user.email,))

def dabut_odm_uzdevumu_pec_id(uzdevuma_id):
    vaicajums = "SELECT * FROM odm_uzdevumi WHERE id = %s"

    return vaicat_db(vaicajums, (uzdevuma_id,))

def dabut_sensoru_koordinatas_pec_uzdevuma_id(uzdevuma_id):
    vaicajums = "SELECT * FROM sensoru_koordinatas WHERE uzdevuma_id = %s"

    return vaicat_db(vaicajums, (uzdevuma_id,), dabut_vienu=False)

### Izveides funkcijas
def izveidot_lietotaju(projekta_id):
    vaicajums = "INSERT INTO lietotaji (projekta_id, epasts) VALUES (%s, %s)"

    vaicat_db(vaicajums, (projekta_id, st.user.email,), rediget_rindu=True)

def izveidot_odm_uzdevumu(uzdevuma_id, datums):
    vaicajums = "INSERT INTO odm_uzdevumi (id, datums) VALUES (%s, %s)"

    vaicat_db(vaicajums, (uzdevuma_id, datums,), rediget_rindu=True)

def izveidot_sensoru_koordinatas(uzdevuma_id, sensora_id, koordinatas):
    vaicajums = "INSERT INTO sensoru_koordinatas (uzdevuma_id, sensora_id, platums, garums) VALUES (%s, %s, %s, %s)"

    vaicat_db(vaicajums, (uzdevuma_id, sensora_id, koordinatas[0], koordinatas[1],), rediget_rindu=True)

### Atjaunināšanas funkcijas
def atjauninat_odm_uzdevuma_datumu_pec_id(uzdevuma_id, datums):
    vaicajums = "UPDATE odm_uzdevumi SET datums = %s WHERE id = %s"

    return vaicat_db(vaicajums, (datums, uzdevuma_id,), rediget_rindu=True)

def atjauninat_sensora_koordinatas_pec_id(uzdevuma_id, sensora_id, koordinatas):
    vaicajums = "UPDATE sensoru_koordinatas SET platums = %s, garums = %s WHERE uzdevuma_id = %s AND sensora_id = %s"

    vaicat_db(vaicajums, (koordinatas[0], koordinatas[1], uzdevuma_id, sensora_id,), rediget_rindu=True)

### Dzēšanas funkcijas
def dzest_sensora_koordinatas_pec_uzdevuma_id(uzdevuma_id):
    vaicajums = "DELETE FROM sensoru_koordinatas WHERE uzdevuma_id IN (%s)"

    vaicat_db(vaicajums, (uzdevuma_id,), rediget_rindu=True)

def dzest_odm_uzdevumu_pec_id(uzdevuma_id):
    vaicajums = "DELETE FROM odm_uzdevumi WHERE id IN (%s)"

    vaicat_db(vaicajums, (uzdevuma_id,), rediget_rindu=True)
