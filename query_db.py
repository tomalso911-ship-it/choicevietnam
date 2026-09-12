import sqlite3
conn = sqlite3.connect('agi_pm.db')
cur = conn.cursor()

# 查看 gs_comm_usd 相关数据
cur.execute("SELECT contract_date, gs_comm_usd FROM won_projects WHERE gs_comm_usd > 0 ORDER BY contract_date")
print("Contract dates with gs_comm_usd > 0:")
for row in cur.fetchall():
    print(row)
