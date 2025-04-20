import streamlit as st
from psycopg2 import connect, sql, extras

@st.cache_resource
def db_savienojums():
    db = st.secrets["postgres_db"]

    return connect(
        host=db["host"],
        dbname=db["datu_baze"],
        user=db["lietotajs"],
        password=db["parole"],
        port=db["port"]
    )

def vaicat_db(vaicajums, argumenti=(), dabut_vienu=True, izveidot_rindu=False):
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

            if izveidot_rindu:
                savienojums.commit()
            else:
                return cursor.fetchone() if dabut_vienu else cursor.fetchall()
    except Exception as e:
        st.error(f"Kļūda datu bāzes vaicājumā: {e}")

def dabut_lietotaju_pec_epasta():
    vaicajums = "SELECT * FROM lietotaji WHERE epasts = %s"

    return vaicat_db(vaicajums, (st.experimental_user.email,))

def vai_pilnvarots_epasts():
    vaicajums = "SELECT * FROM autorizeti_epasti WHERE epasts = %s"

    rezultats = vaicat_db(vaicajums, (st.experimental_user.email,))

    return rezultats is not None

def izveidot_lietotaju(projekta_id):
    vaicajums = "INSERT INTO lietotaji (projekta_id, epasts) VALUES (%s, %s)"

    vaicat_db(vaicajums, (projekta_id, st.experimental_user.email,), izveidot_rindu=True)
