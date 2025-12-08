import frappe
from frappe import _
import json

@frappe.whitelist()
def get_events(start=None, end=None, month_start=None, month_end=None, filters=None, employee_filters=None, shift_filters=None):
    """
    Robust Version: Handles both 'start/end' (Standard Calendar) and 'month_start/month_end' (Roster API).
    """
    
    # 1. ARGUMENT NORMALIZATION (The Fix for your TypeError)
    # The Roster API sends month_start/month_end. We map them to start/end.
    if not start and month_start:
        start = month_start
    if not end and month_end:
        end = month_end

    # If we still don't have dates, return empty to prevent crash
    if not start or not end:
        return []

    # 2. Get current user and roles
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    
    # DEFINITION OF MANAGER
    management_roles = ['HR Manager', 'System Manager', 'Administrator', 'Shift Manager']
    has_management_access = any(role in management_roles for role in user_roles)
    
    # 3. Parse Filters
    # The Roster API sends filters inside 'employee_filters' or 'shift_filters' dictionaries.
    # We merge them into a single 'filters' dict for easier processing.
    if not filters:
        filters = {}
    elif isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except:
            filters = {}

    # Merge Roster API specific filters if they exist
    if employee_filters:
        if isinstance(employee_filters, str):
            employee_filters = json.loads(employee_filters)
        filters.update(employee_filters)
        
    if shift_filters:
        if isinstance(shift_filters, str):
            shift_filters = json.loads(shift_filters)
        filters.update(shift_filters)
    
    # 4. Build base conditions
    conditions = [
        "`tabShift Assignment`.docstatus < 2",
        "`tabShift Assignment`.status = 'Active'"
    ]
    
    # CRITICAL: Publication filter for non-managers
    # IFNULL checks if the checkbox is NULL (untouched) and treats it as 0 (Hidden)
    if not has_management_access:
        conditions.append("IFNULL(`tabShift Assignment`.custom_published, 0) = 1")
    
    # 5. Apply SQL Filters
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
    
    where_clause = " AND ".join(conditions)
    
    # 6. Fetch Data
    # Note: We do NOT fetch custom_first_aider etc. here to avoid 500 errors if fields are missing.
    # We strictly focus on the 'custom_published' column.
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
    
    # 7. Format Events
    events = []
    for shift in shifts:
        title = f"{shift.employee_name} ({shift.shift_type})"
        
        # Color Logic: Green for Published, Orange for Unpublished
        if shift.custom_published:
             bg_color = '#28a745' # Green
        else:
             bg_color = '#fd7e14' # Orange

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
