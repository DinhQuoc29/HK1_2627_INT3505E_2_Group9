"""Tạo mẫu 5% user từ dữ liệu gốc REES46 (tháng 12/2019 và 1/2020) cho notebook mô hình.

Đặt file gốc vào data/ (2019-Dec.csv.gz, 2020-Jan.csv.gz; .csv hoặc .parquet cũng được) rồi chạy:

    python prepare_data.py

Kết quả: data/2019-Dec_5pct.parquet và data/2020-Jan_5pct.parquet.

Lấy mẫu THEO USER bằng hash(user_id) % 100 < 5: một user được chọn thì toàn bộ lịch sử của user
đó ở cả hai tháng đều được giữ (cần cho feature lịch sử). Dùng DuckDB để đọc file nhiều GB mà
không cần nạp hết vào RAM.
"""
import argparse
import os
import time
from pathlib import Path

import duckdb

MONTHS = ["2019-Dec", "2020-Jan"]


def find_raw(data_dir: Path, month: str):
    for ext in (".csv.gz", ".csv", ".parquet"):
        p = data_dir / f"{month}{ext}"
        if p.exists():
            return p
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--pct", type=int, default=5, help="phần trăm user giữ lại (mặc định 5)")
    ap.add_argument("--memory", default="4GB", help="giới hạn RAM cho DuckDB, giảm nếu máy yếu")
    ap.add_argument("--force", action="store_true", help="tạo lại kể cả khi file mẫu đã có")
    a = ap.parse_args()

    data_dir = Path(a.data_dir)
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{a.memory}'")
    con.execute(f"SET temp_directory='{(data_dir / 'duckdb_tmp').as_posix()}'")   # tràn ra đĩa khi thiếu RAM

    for month in MONTHS:
        out = data_dir / f"{month}_{a.pct}pct.parquet"
        if out.exists() and not a.force:
            print(f"Đã có {out}, bỏ qua (dùng --force để tạo lại)")
            continue
        src = find_raw(data_dir, month)
        if src is None:
            print(f"THIẾU dữ liệu gốc: đặt {month}.csv.gz (hoặc .csv / .parquet) vào {data_dir}/")
            continue

        if src.suffix == ".parquet":
            read = f"SELECT * FROM read_parquet('{src.as_posix()}')"
        else:   # REES46 ghi thời gian dạng '2019-12-01 00:00:00 UTC'
            read = (f"SELECT * REPLACE (CAST(replace(event_time, ' UTC', '') AS TIMESTAMP) AS event_time) "
                    f"FROM read_csv_auto('{src.as_posix()}', types={{'event_time': 'VARCHAR', 'user_session': 'VARCHAR'}})")
        t = time.time()
        con.execute(f"COPY (SELECT * FROM ({read}) WHERE hash(user_id) % 100 < {a.pct}) "
                    f"TO '{out.as_posix()}' (FORMAT parquet)")
        n, u = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT user_id) FROM read_parquet('{out.as_posix()}')").fetchone()
        print(f"{src.name} -> {out.name}: {n:,} sự kiện, {u:,} user, {os.path.getsize(out) / 1e6:.0f} MB, {time.time() - t:.0f}s")


if __name__ == "__main__":
    import sys
    for stream in (sys.stdout, sys.stderr):      # Windows: in được tiếng Việt
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    main()
