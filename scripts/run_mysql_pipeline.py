import subprocess
import os
import sys

BASE_DIR = r"e:\DBMS"
SQL_DIR = os.path.join(BASE_DIR, "sql")
MYSQL_BIN = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
HOST = "127.0.0.1"
PORT = "3307"
USER = "root"

scripts = [
    ("01_schema.sql", None),
    ("02_views.sql", "supply_chain_db"),
    ("03_procedures_triggers.sql", "supply_chain_db"),
    ("02_sample_data.sql", "supply_chain_db"),
    ("04_analytical_queries.sql", "supply_chain_db"),
]

def run_script(filename, db=None):
    filepath = os.path.join(SQL_DIR, filename)
    print(f"\n==================================================")
    print(f"Executing MySQL CLI on: {filename}")
    print(f"==================================================")
    cmd = [MYSQL_BIN, "-h", HOST, "-P", PORT, "-u", USER]
    if db:
        cmd.append(db)
        
    with open(filepath, "r", encoding="utf-8") as f:
        sql_content = f.read()

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    stdout, stderr = proc.communicate(input=sql_content)

    if stdout.strip():
        print("[STDOUT]:")
        # Print first 25 lines if long
        lines = stdout.strip().split("\n")
        print("\n".join(lines[:25]))
        if len(lines) > 25:
            print(f"... and {len(lines) - 25} more rows.")

    if stderr.strip():
        print(f"[STDERR]:\n{stderr}")

    if proc.returncode != 0:
        print(f"FAILED with returncode {proc.returncode}")
        return False
    else:
        print(f"SUCCESS: {filename} executed cleanly.")
        return True

def main():
    print("Starting Automated MySQL Execution Pipeline...")
    for filename, db in scripts:
        ok = run_script(filename, db)
        if not ok:
            print("Pipeline aborted due to error.")
            sys.exit(1)

    print("\n==================================================")
    print("ALL MYSQL CLI AUTOMATION SCRIPTS COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()
