import frappe
from frappe import _
import json

@frappe.whitelist()
def get_events(start=None, end=None, month_start=None, month_end=None, filters=None, employee_filters=None, shift_filters=None):
    if not start and month_start:
        start = month_start
    if not end and month_end:
        end = month_end

    if not start or not end:
        return []

    # --- 1. Filter Parsing ---
    if not filters: filters = {}
    elif isinstance(filters, str):
        try: filters = json.loads(filters)
        except: filters = {}

    if employee_filters:
        if isinstance(employee_filters, str):
            try: employee_filters = json.loads(employee_filters)
            except: employee_filters = {}
        filters.update(employee_filters)

    if shift_filters:
        if isinstance(shift_filters, str):
            try: shift_filters = json.loads(shift_filters)
            except: shift_filters = {}
        filters.update(shift_filters)

    # --- 2. Build Conditions ---
    conditions = [
        "`tabShift Assignment`.docstatus < 2",
        "`tabShift Assignment`.status = 'Active'"
    ]
    values = {'start': start, 'end': end}

    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    management_roles = ['HR Manager', 'System Manager', 'Administrator', 'Shift Manager']
    has_management_access = any(role in management_roles for role in user_roles)

    if not has_management_access:
        conditions.append("IFNULL(`tabShift Assignment`.custom_published, 0) = 1")

    # Dynamic filters
    for field in ['company', 'department', 'designation', 'employee', 'shift_type']:
        if filters.get(field):
            conditions.append(f"`tabShift Assignment`.{field} = %({field})s")
            values[field] = filters.get(field)

    where_clause = " AND ".join(conditions)

    # --- 3. SQL QUERY (FIXED: Added JOIN to Shift Type for color) ---
    try:
        shifts = frappe.db.sql(f"""
            SELECT 
                `tabShift Assignment`.name,
                `tabShift Assignment`.employee,
                `tabShift Assignment`.employee_name,
                `tabShift Assignment`.shift_type,
                `tabShift Assignment`.start_date,
                `tabShift Assignment`.end_date,
                `tabShift Assignment`.status,
                `tabShift Assignment`.custom_published,
                `tabShift Assignment`.company,
                `tabShift Assignment`.department,
                `tabShift Assignment`.shift_location,
                `tabShift Type`.color as color
            FROM 
                `tabShift Assignment`
            LEFT JOIN
                `tabShift Type` ON `tabShift Assignment`.shift_type = `tabShift Type`.name
            WHERE 
                {where_clause}
                AND (
                    (`tabShift Assignment`.start_date BETWEEN %(start)s AND %(end)s)
                    OR (`tabShift Assignment`.end_date BETWEEN %(start)s AND %(end)s)
                    OR (`tabShift Assignment`.start_date <= %(start)s AND `tabShift Assignment`.end_date >= %(end)s)
                )
            ORDER BY 
                `tabShift Assignment`.start_date, 
                `tabShift Assignment`.employee_name
        """, values, as_dict=True)
    except Exception as e:
        frappe.log_error(f"Roster Query Error: {str(e)}", "Pro Coaching Error")
        return []

    # --- 4. Format Response ---
    events = []
    for shift in shifts:
        title = f"{shift.employee_name} ({shift.shift_type})"
        
        # Safe Date Conversion (Prevent JSON serialization errors)
        s_date = str(shift.start_date)
        e_date = str(shift.end_date)

        event = {
            'name': shift.name,
            'id': shift.name,
            'title': title,
            'subject': title,
            'employee': shift.employee,
            'employee_name': shift.employee_name,
            'shift_type': shift.shift_type,
            'shift_location': shift.shift_location or '',
            'start': s_date,
            'end': e_date,
            'allDay': True,
            'doctype': 'Shift Assignment',
            'status': shift.status,
            'color': shift.color or '#3788d8' # Fallback Blue if color is missing
        }
        events.append(event)

    return events
