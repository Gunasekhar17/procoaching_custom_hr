@frappe.whitelist()
def get_events(start=None, end=None, month_start=None, month_end=None, filters=None, employee_filters=None, shift_filters=None):
    import json
    
    # --- 1. Date Logic ---
    if not start and month_start: start = month_start
    if not end and month_end: end = month_end
    if not start or not end: return []

    # --- 2. Filter Parsing (Safe Method) ---
    def parse_json(f):
        if not f: return {}
        if isinstance(f, str):
            try: return json.loads(f)
            except: return {}
        return f

    filters = parse_json(filters)
    filters.update(parse_json(employee_filters))
    filters.update(parse_json(shift_filters))

    # --- 3. Build Conditions ---
    conditions = ["`tabShift Assignment`.docstatus < 2", "`tabShift Assignment`.status = 'Active'"]
    values = {'start': start, 'end': end}

    # Permissions Check
    user = frappe.session.user
    if user != 'Administrator':
        roles = frappe.get_roles(user)
        management_roles = ['HR Manager', 'System Manager', 'Administrator', 'Shift Manager']
        if not any(r in management_roles for r in roles):
            conditions.append("IFNULL(`tabShift Assignment`.custom_published, 0) = 1")

    # Apply Filters
    for field in ['company', 'department', 'designation', 'employee', 'shift_type']:
        if filters.get(field):
            conditions.append(f"`tabShift Assignment`.{field} = %({field})s")
            values[field] = filters.get(field)

    where_clause = " AND ".join(conditions)

    # --- 4. Fetch Shifts (Standard Query - NO JOIN to avoid crashes) ---
    try:
        shifts = frappe.db.sql(f"""
            SELECT 
                name, employee, employee_name, shift_type, start_date, end_date,
                status, company, department, shift_location
            FROM `tabShift Assignment`
            WHERE {where_clause}
            AND (
                (start_date BETWEEN %(start)s AND %(end)s) OR 
                (end_date BETWEEN %(start)s AND %(end)s) OR 
                (start_date <= %(start)s AND end_date >= %(end)s)
            )
            ORDER BY start_date, employee_name
        """, values, as_dict=True)
    except Exception as e:
        frappe.log_error(f"Roster Query Failed: {str(e)}", "Roster Error")
        return []

    # --- 5. Fetch Colors Safely (The Fix) ---
    # We fetch colors separately to handle different column names (color vs custom_color)
    shift_colors = {}
    try:
        # Try standard field name
        types = frappe.get_all("Shift Type", fields=["name", "color"])
        for t in types: shift_colors[t.name] = t.get("color")
    except:
        try:
            # Fallback to custom field name
            types = frappe.get_all("Shift Type", fields=["name", "custom_color"])
            for t in types: shift_colors[t.name] = t.get("custom_color")
        except:
            pass 

    # --- 6. Format Response ---
    events = []
    for shift in shifts:
        title = f"{shift.employee_name} ({shift.shift_type})"
        
        # 1. Get Color (Use default Blue if missing to prevent crash)
        assigned_color = shift_colors.get(shift.shift_type)
        if not assigned_color:
            assigned_color = '#3788d8' 

        event = {
            'name': shift.name,
            'id': shift.name,
            'title': title,
            'subject': title,
            'employee': shift.employee,
            'employee_name': shift.employee_name,
            'shift_type': shift.shift_type,
            'shift_location': shift.shift_location or '',
            'start': str(shift.start_date),
            'end': str(shift.end_date),
            'allDay': True,
            'doctype': 'Shift Assignment',
            'status': shift.status,
            'color': assigned_color # This is now guaranteed to have a value
        }
        events.append(event)

    return events
