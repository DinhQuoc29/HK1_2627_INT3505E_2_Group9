"""Model SQLAlchemy phải khớp schema do migration tạo (tên bảng, cột, nullable, PK)."""
import sqlalchemy as sa

from db import Base, engine


def test_models_match_database():
    insp = sa.inspect(engine)
    db_tables = set(insp.get_table_names())
    problems = []
    for name, table in Base.metadata.tables.items():
        if name not in db_tables:
            problems.append(f"{name}: không có trong DB")
            continue
        db_cols = {c["name"]: c for c in insp.get_columns(name)}
        if set(db_cols) != set(table.c.keys()):
            problems.append(f"{name}: cột lệch {set(db_cols) ^ set(table.c.keys())}")
            continue
        for col in table.c:
            if col.nullable != db_cols[col.name]["nullable"] and not col.primary_key:
                problems.append(f"{name}.{col.name}: nullable lệch")
        pk = set(insp.get_pk_constraint(name)["constrained_columns"])
        if pk != {c.name for c in table.primary_key.columns}:
            problems.append(f"{name}: PK lệch")
    assert not problems, "\n".join(problems)
