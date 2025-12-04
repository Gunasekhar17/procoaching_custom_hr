import frappe
from frappe import _
import json

@frappe.whitelist()
def get_events(start, end, filters=None):
    """
    Roster Override Logic:
    1. HR Managers / System Managers: View ALL shifts (Published & Unpublished).
       - Published = Green
       - Unpublished = Orange
    2. Staff / Employees: View ONLY Published shifts.
       - Unpublished shifts are strictly hidden via SQL.
    """
    
    # Get current user and roles
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    
    # DEFINITION: Who sees Unpublished (Orange) shifts?
    # HR Manager, System Manager, Administrator, Shift Manager
    management_roles = ['HR Manager', 'System Manager', 'Administrator', 'Shift Manager']
    has_management_access = any(role in management_roles for role in user_roles)
    
    # Parse filters
    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except:
            filters = {}
    elif not filters:
        filters = {}
    
    # Build base conditions
    conditions = [
        "`tabShift Assignment`.docstatus < 2",
        "`tabShift Assignment`.status = 'Active'"
    ]
    
    # CRITICAL LOGIC: Staff Visibility
    # If the user is NOT a manager, enforce that they can only see Published shifts.
    # We use IFNULL to treat NULL (untouched checkboxes) as 0 (Unpublished).
    if not has_management_access:
        conditions.append("IFNULL(`tabShift Assignment`.custom_published, 0) = 1")
    
    # Add optional filters from roster UI
    if filters.get('company'):
        conditions.append(f"`tabShift Assignment`.company = {frappe.db.escape(filters.get('company'))}")
    if filters.get('department'):
        conditions.append(f"`tabShift Assignment`.department = {frappe.db.escape(filters.get('department'))}")
    if filters.get('designation'):
        conditions.append(f"`tabShift Assignment`.designation = {frappe.db.escape(filters.get('designation'))}")
    if filters.get('employee'):
        conditions.append(f"`tabShift Assignment`.employee = {frappe.db.escape(filters.get('employee'))}")
    if filters.get('shift_type'):
        conditions.append(f"`tabShift Assignment`.shift_type = {frappe.db.escape(filters.get('shift_type'))}")
    
    # Build WHERE clause
    where_clause = " AND ".join(conditions)
    
    # Fetch shifts WITHOUT the missing custom columns (to prevent 500 errors)
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
            `tabShift Assignment`.color
        FROM 
            `tabShift Assignment`
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
    """, {
        'start': start,
        'end': end
    }, as_dict=True)
    
    # Format events for calendar display
    events = []
    for shift in shifts:
        # Combined Title
        title = f"{shift.employee_name} ({shift.shift_type})"
        
        # Determine Color
        # Green (#28a745) for published, Orange (#fd7e14) for unpublished
        if shift.custom_published:
             bg_color = '#28a745' # Green
        else:
             bg_color = '#fd7e14' # Orange

        # Create event
        event = {
            'name': shift.name,
            'id': shift.name,
            'title': title,
            'subject': title,
            'employee': shift.employee,
            'employee_name': shift.employee_name,
            'shift_type': shift.shift_type,
            'start': str(shift.start_date),
            'end': str(shift.end_date),
            'allDay': True,
            'doctype': 'Shift Assignment',
            'status': shift.status,
            'backgroundColor': bg_color,
            'borderColor': bg_color,
            'textColor': '#ffffff'
        }
        events.append(event)
    
    return events
