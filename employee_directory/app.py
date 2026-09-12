from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort
)
import sqlite3
import json
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "employee-directory-secret-key"

DATABASE = "employees.db"


# =========================================================
# 資料庫
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 員工資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_no TEXT NOT NULL UNIQUE,
            chinese_name TEXT NOT NULL,
            english_name TEXT NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            extension TEXT NOT NULL,
            mobile TEXT NOT NULL,
            office_location TEXT NOT NULL,
            hire_date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # 異動紀錄
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL,
            operation_time TEXT NOT NULL,
            operator TEXT NOT NULL,
            employee_no TEXT,
            before_data TEXT,
            after_data TEXT,
            result TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT
        )
    """)

    conn.commit()
    conn.close()

    # 如果沒有資料，建立 20 筆虛擬員工
    seed_employees()


def seed_employees():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        return

    employees = [
        (
            "EMP001", "王小明", "Ming Wang", "資訊部",
            "系統工程師", "ming.wang@example.com", "1001",
            "0912000001", "台北辦公室", "2022-01-10", "在職"
        ),
        (
            "EMP002", "陳美華", "Mei-Hua Chen", "人資部",
            "人資專員", "mei.chen@example.com", "1002",
            "0912000002", "台北辦公室", "2021-03-15", "在職"
        ),
        (
            "EMP003", "林志豪", "Chih-Hao Lin", "財務部",
            "財務分析師", "chihhao.lin@example.com", "1003",
            "0912000003", "台北辦公室", "2020-07-20", "在職"
        ),
        (
            "EMP004", "張雅婷", "Ya-Ting Chang", "行銷部",
            "行銷專員", "yating.chang@example.com", "1004",
            "0912000004", "台北辦公室", "2023-02-01", "在職"
        ),
        (
            "EMP005", "李冠廷", "Kuan-Ting Lee", "業務部",
            "業務經理", "kuanting.lee@example.com", "1005",
            "0912000005", "台中辦公室", "2019-11-05", "在職"
        ),
        (
            "EMP006", "黃怡君", "Yi-Chun Huang", "資訊部",
            "前端工程師", "yichun.huang@example.com", "1006",
            "0912000006", "台北辦公室", "2022-05-16", "在職"
        ),
        (
            "EMP007", "吳承翰", "Cheng-Han Wu", "資訊部",
            "後端工程師", "chenghan.wu@example.com", "1007",
            "0912000007", "高雄辦公室", "2021-08-23", "在職"
        ),
        (
            "EMP008", "蔡佩珊", "Pei-Shan Tsai", "客服部",
            "客服專員", "peishan.tsai@example.com", "1008",
            "0912000008", "台北辦公室", "2023-06-12", "在職"
        ),
        (
            "EMP009", "劉俊傑", "Chun-Chieh Liu", "研發部",
            "研發工程師", "chunchieh.liu@example.com", "1009",
            "0912000009", "新竹辦公室", "2020-04-06", "在職"
        ),
        (
            "EMP010", "許芳瑜", "Fang-Yu Hsu", "法務部",
            "法務專員", "fangyu.hsu@example.com", "1010",
            "0912000010", "台北辦公室", "2021-09-01", "在職"
        ),
        (
            "EMP011", "鄭宇翔", "Yu-Hsiang Cheng", "資訊部",
            "DevOps 工程師", "yuhsiang.cheng@example.com", "1011",
            "0912000011", "台北辦公室", "2022-10-17", "在職"
        ),
        (
            "EMP012", "周欣怡", "Hsin-Yi Chou", "設計部",
            "UI/UX 設計師", "hsinyi.chou@example.com", "1012",
            "0912000012", "台北辦公室", "2023-01-09", "在職"
        ),
        (
            "EMP013", "謝宗翰", "Tsung-Han Hsieh", "業務部",
            "業務專員", "tsunghan.hsieh@example.com", "1013",
            "0912000013", "台中辦公室", "2022-03-28", "在職"
        ),
        (
            "EMP014", "曾婉婷", "Wan-Ting Tseng", "人資部",
            "招募專員", "wanting.tseng@example.com", "1014",
            "0912000014", "台北辦公室", "2020-12-14", "在職"
        ),
        (
            "EMP015", "洪偉哲", "Wei-Che Hung", "研發部",
            "軟體工程師", "weiche.hung@example.com", "1015",
            "0912000015", "新竹辦公室", "2019-06-03", "在職"
        ),
        (
            "EMP016", "郭怡伶", "Yi-Ling Kuo", "財務部",
            "會計專員", "yiling.kuo@example.com", "1016",
            "0912000016", "台北辦公室", "2021-02-22", "在職"
        ),
        (
            "EMP017", "林柏宇", "Po-Yu Lin", "行銷部",
            "行銷經理", "poyu.lin@example.com", "1017",
            "0912000017", "台北辦公室", "2018-10-15", "在職"
        ),
        (
            "EMP018", "趙思妤", "Szu-Yu Chao", "客服部",
            "客服主管", "szuyu.chao@example.com", "1018",
            "0912000018", "高雄辦公室", "2019-05-20", "在職"
        ),
        (
            "EMP019", "何明哲", "Ming-Che Ho", "資訊部",
            "資料庫工程師", "mingche.ho@example.com", "1019",
            "0912000019", "台北辦公室", "2020-08-10", "在職"
        ),
        (
            "EMP020", "蘇怡安", "Yi-An Su", "行政部",
            "行政專員", "yian.su@example.com", "1020",
            "0912000020", "台中辦公室", "2022-11-21", "在職"
        )
    ]

    cursor.executemany("""
        INSERT INTO employees (
            employee_no,
            chinese_name,
            english_name,
            department,
            position,
            email,
            extension,
            mobile,
            office_location,
            hire_date,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, employees)

    conn.commit()
    conn.close()


# =========================================================
# 工具函式
# =========================================================

def employee_to_dict(employee):
    if employee is None:
        return None

    return {
        "employee_no": employee["employee_no"],
        "chinese_name": employee["chinese_name"],
        "english_name": employee["english_name"],
        "department": employee["department"],
        "position": employee["position"],
        "email": employee["email"],
        "extension": employee["extension"],
        "mobile": employee["mobile"],
        "office_location": employee["office_location"],
        "hire_date": employee["hire_date"],
        "status": employee["status"]
    }


def get_client_ip():
    # 若使用 Proxy，優先取得 X-Forwarded-For
    forwarded = request.headers.get("X-Forwarded-For")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.remote_addr or "Unknown"


def write_log(
    operation,
    operator,
    employee_no,
    before_data,
    after_data,
    result
):
    conn = get_db()

    conn.execute("""
        INSERT INTO audit_logs (
            operation,
            operation_time,
            operator,
            employee_no,
            before_data,
            after_data,
            result,
            ip_address,
            user_agent
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        operation,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        operator,
        employee_no,
        json.dumps(before_data, ensure_ascii=False)
        if before_data else None,
        json.dumps(after_data, ensure_ascii=False)
        if after_data else None,
        result,
        get_client_ip(),
        request.headers.get("User-Agent", "Unknown")
    ))

    conn.commit()
    conn.close()


def validate_employee_form(form):
    errors = []

    employee_no = form.get("employee_no", "").strip()
    chinese_name = form.get("chinese_name", "").strip()
    english_name = form.get("english_name", "").strip()
    department = form.get("department", "").strip()
    position = form.get("position", "").strip()
    email = form.get("email", "").strip()
    extension = form.get("extension", "").strip()
    mobile = form.get("mobile", "").strip()
    office_location = form.get("office_location", "").strip()
    hire_date = form.get("hire_date", "").strip()
    status = form.get("status", "").strip()

    if not employee_no:
        errors.append("員工編號不可為空白。")

    if not chinese_name:
        errors.append("中文姓名不可為空白。")

    if not english_name:
        errors.append("英文姓名不可為空白。")

    if not department:
        errors.append("所屬部門不可為空白。")

    if not position:
        errors.append("職稱不可為空白。")

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.match(email_pattern, email):
        errors.append("電子郵件格式不正確。")

    if not re.match(r"^\d{4}$", extension):
        errors.append("分機號碼必須為 4 位數字。")

    if not re.match(r"^09\d{8}$", mobile):
        errors.append("行動電話格式必須為 09 開頭的 10 位數字。")

    if not hire_date:
        errors.append("到職日期不可為空白。")

    if status not in ["在職", "離職", "留職停薪"]:
        errors.append("在職狀態不正確。")

    return errors


def form_to_tuple(form):
    return (
        form.get("employee_no", "").strip(),
        form.get("chinese_name", "").strip(),
        form.get("english_name", "").strip(),
        form.get("department", "").strip(),
        form.get("position", "").strip(),
        form.get("email", "").strip(),
        form.get("extension", "").strip(),
        form.get("mobile", "").strip(),
        form.get("office_location", "").strip(),
        form.get("hire_date", "").strip(),
        form.get("status", "").strip()
    )


# =========================================================
# 前台：員工清單
# =========================================================

@app.route("/")
def index():
    keyword = request.args.get("keyword", "").strip()
    department = request.args.get("department", "").strip()
    status = request.args.get("status", "").strip()

    conn = get_db()

    sql = "SELECT * FROM employees WHERE 1=1"
    params = []

    if keyword:
        sql += """
            AND (
                employee_no LIKE ?
                OR chinese_name LIKE ?
                OR english_name LIKE ?
                OR department LIKE ?
                OR position LIKE ?
                OR email LIKE ?
            )
        """

        search = f"%{keyword}%"

        params.extend([
            search,
            search,
            search,
            search,
            search,
            search
        ])

    if department:
        sql += " AND department = ?"
        params.append(department)

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY employee_no ASC"

    employees = conn.execute(sql, params).fetchall()

    departments = conn.execute("""
        SELECT DISTINCT department
        FROM employees
        ORDER BY department
    """).fetchall()

    conn.close()

    return render_template(
        "employees.html",
        employees=employees,
        departments=departments,
        keyword=keyword,
        selected_department=department,
        selected_status=status
    )


# =========================================================
# 前台：新增員工
# =========================================================

@app.route("/employees/new", methods=["GET", "POST"])
def create_employee():

    if request.method == "POST":

        errors = validate_employee_form(request.form)

        if errors:
            for error in errors:
                flash(error, "danger")

            return render_template(
                "employee_form.html",
                employee=request.form,
                mode="新增"
            )

        data = form_to_tuple(request.form)

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO employees (
                    employee_no,
                    chinese_name,
                    english_name,
                    department,
                    position,
                    email,
                    extension,
                    mobile,
                    office_location,
                    hire_date,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

            conn.commit()

            employee_no = data[0]

            conn.close()

            write_log(
                operation="新增",
                operator="admin",
                employee_no=employee_no,
                before_data=None,
                after_data=dict(zip([
                    "employee_no",
                    "chinese_name",
                    "english_name",
                    "department",
                    "position",
                    "email",
                    "extension",
                    "mobile",
                    "office_location",
                    "hire_date",
                    "status"
                ], data)),
                result="成功"
            )

            flash("員工資料新增成功。", "success")

            return redirect(url_for("index"))

        except sqlite3.IntegrityError:
            conn.close()

            flash(
                "新增失敗：員工編號或電子郵件可能已經存在。",
                "danger"
            )

            return render_template(
                "employee_form.html",
                employee=request.form,
                mode="新增"
            )

    return render_template(
        "employee_form.html",
        employee=None,
        mode="新增"
    )


# =========================================================
# 前台：員工詳細資料
# =========================================================

@app.route("/employees/<int:employee_id>")
def employee_detail(employee_id):

    conn = get_db()

    employee = conn.execute("""
        SELECT *
        FROM employees
        WHERE id = ?
    """, (employee_id,)).fetchone()

    conn.close()

    if employee is None:
        abort(404)

    return render_template(
        "employee_detail.html",
        employee=employee
    )


# =========================================================
# 前台：修改員工
# =========================================================

@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
def edit_employee(employee_id):

    conn = get_db()

    employee = conn.execute("""
        SELECT *
        FROM employees
        WHERE id = ?
    """, (employee_id,)).fetchone()

    conn.close()

    if employee is None:
        abort(404)

    if request.method == "POST":

        errors = validate_employee_form(request.form)

        if errors:
            for error in errors:
                flash(error, "danger")

            return render_template(
                "employee_form.html",
                employee=request.form,
                mode="修改"
            )

        data = form_to_tuple(request.form)

        before_data = employee_to_dict(employee)

        conn = get_db()

        try:

            conn.execute("""
                UPDATE employees
                SET
                    employee_no = ?,
                    chinese_name = ?,
                    english_name = ?,
                    department = ?,
                    position = ?,
                    email = ?,
                    extension = ?,
                    mobile = ?,
                    office_location = ?,
                    hire_date = ?,
                    status = ?
                WHERE id = ?
            """, (*data, employee_id))

            conn.commit()

            updated_employee = conn.execute("""
                SELECT *
                FROM employees
                WHERE id = ?
            """, (employee_id,)).fetchone()

            conn.close()

            after_data = employee_to_dict(updated_employee)

            write_log(
                operation="修改",
                operator="admin",
                employee_no=data[0],
                before_data=before_data,
                after_data=after_data,
                result="成功"
            )

            flash("員工資料修改成功。", "success")

            return redirect(
                url_for(
                    "employee_detail",
                    employee_id=employee_id
                )
            )

        except sqlite3.IntegrityError:
            conn.close()

            flash(
                "修改失敗：員工編號或電子郵件可能已經存在。",
                "danger"
            )

            return render_template(
                "employee_form.html",
                employee=request.form,
                mode="修改"
            )

    return render_template(
        "employee_form.html",
        employee=employee,
        mode="修改"
    )


# =========================================================
# 前台：刪除員工
# =========================================================

@app.route("/employees/<int:employee_id>/delete", methods=["POST"])
def delete_employee(employee_id):

    conn = get_db()

    employee = conn.execute("""
        SELECT *
        FROM employees
        WHERE id = ?
    """, (employee_id,)).fetchone()

    if employee is None:
        conn.close()
        abort(404)

    before_data = employee_to_dict(employee)
    employee_no = employee["employee_no"]

    try:

        conn.execute("""
            DELETE FROM employees
            WHERE id = ?
        """, (employee_id,))

        conn.commit()
        conn.close()

        write_log(
            operation="刪除",
            operator="admin",
            employee_no=employee_no,
            before_data=before_data,
            after_data=None,
            result="成功"
        )

        flash(
            f"員工 {employee_no} 已成功刪除。",
            "success"
        )

    except Exception as e:

        conn.close()

        write_log(
            operation="刪除",
            operator="admin",
            employee_no=employee_no,
            before_data=before_data,
            after_data=None,
            result=f"失敗：{str(e)}"
        )

        flash(
            "刪除失敗，請稍後再試。",
            "danger"
        )

    return redirect(url_for("index"))


# =========================================================
# 後台：異動紀錄
# =========================================================

@app.route("/admin/logs")
def audit_logs():

    keyword = request.args.get("keyword", "").strip()
    operation = request.args.get("operation", "").strip()
    sort = request.args.get("sort", "newest")

    conn = get_db()

    sql = "SELECT * FROM audit_logs WHERE 1=1"
    params = []

    if keyword:
        sql += """
            AND (
                employee_no LIKE ?
                OR operator LIKE ?
                OR ip_address LIKE ?
                OR result LIKE ?
            )
        """

        search = f"%{keyword}%"

        params.extend([
            search,
            search,
            search,
            search
        ])

    if operation:
        sql += " AND operation = ?"
        params.append(operation)

    if sort == "oldest":
        sql += " ORDER BY operation_time ASC, id ASC"
    elif sort == "employee":
        sql += " ORDER BY employee_no ASC, operation_time DESC"
    else:
        sql += " ORDER BY operation_time DESC, id DESC"

    logs = conn.execute(sql, params).fetchall()

    conn.close()

    return render_template(
        "logs.html",
        logs=logs,
        keyword=keyword,
        selected_operation=operation,
        selected_sort=sort
    )


# =========================================================
# 啟動程式
# =========================================================

if __name__ == "__main__":
    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
