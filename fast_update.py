from database.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("""
        UPDATE predictions
        SET power_score = CASE
            WHEN target_score IN ('0-1', '0-2', '0-3', '1-3') THEN
                LEAST(100.0, ((100.0 - (probability * 100)) * 0.5) + (COALESCE(ai_confidence, 100.0 - (probability * 100)) * 0.5))
            ELSE
                LEAST(100.0, ((probability * 100) * 0.5) + (COALESCE(ai_confidence, probability * 100) * 0.5))
            END
    """))
    conn.commit()
print("Banco atualizado em milissegundos!")
