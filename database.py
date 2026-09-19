import sqlite3
from datetime import datetime
import pandas as pd

DB_NAME = "incidents.db"

def init_db():
    """Inicializa a tabela de incidentes e dados de demonstração."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            image_url TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            address_hint TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    ''')
    
    # Dados de Exemplo
    cursor.execute("SELECT COUNT(*) FROM incidents")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sample_data = [
            ('Alagamento/Inundação', 'Crítico', 'Nível da água atingindo 1 metro na via. Carros ilhados.', 'active', -23.55052, -46.633308, 'Centro - SP', now),
            ('Árvore/Ramo caído', 'Médio', 'Queda de árvore de grande porte interditando meia pista.', 'in_progress', -23.55552, -46.638308, 'Bela Vista - SP', now),
            ('Deslizamento/Risco de desabamento', 'Crítico', 'Rachaduras na encosta do morro. Risco iminente.', 'active', -23.54252, -46.620308, 'Mooca - SP', now),
            ('Fio energizado/Rede elétrica caída', 'Médio', 'Fios de alta tensão caídos na rua após forte vento.', 'resolved', -23.56052, -46.650308, 'Jardins - SP', now)
        ]
        cursor.executemany('''
            INSERT INTO incidents (category, severity, description, status, latitude, longitude, address_hint, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)
    
    conn.commit()
    conn.close()

def add_incident(category, severity, description, image_url, lat, lng, address_hint=""):
    """Insere um novo incidente registrado."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO incidents (category, severity, description, image_url, status, latitude, longitude, address_hint, created_at)
        VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
    ''', (category, severity, description, image_url, lat, lng, address_hint, created_at))
    conn.commit()
    conn.close()

def get_incidents(category_filter="Todas", severity_filter="Todos", status_filter="Todos"):
    """Retorna lista de incidentes filtrados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT id, category, severity, description, image_url, status, latitude, longitude, address_hint, created_at FROM incidents WHERE 1=1"
    params = []
    
    if category_filter != "Todas":
        query += " AND category = ?"
        params.append(category_filter)
        
    if severity_filter != "Todos":
        query += " AND severity = ?"
        params.append(severity_filter)

    if status_filter != "Todos":
        query += " AND status = ?"
        params.append(status_filter)
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    incidents = []
    for r in rows:
        incidents.append({
            "id": r[0],
            "category": r[1],
            "severity": r[2],
            "description": r[3],
            "image_url": r[4],
            "status": r[5],
            "latitude": r[6],
            "longitude": r[7],
            "address_hint": r[8],
            "created_at": r[9]
        })
    return incidents

def update_status(incident_id, new_status):
    """Altera o status do chamado."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        UPDATE incidents
        SET status = ?, updated_at = ?
        WHERE id = ?
    ''', (new_status, updated_at, incident_id))
    conn.commit()
    conn.close()

def get_dataframe():
    """Exporta os dados em formato Pandas DataFrame para download."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM incidents ORDER BY id DESC", conn)
    conn.close()
    return df