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

    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    
    management_roles = ['HR Manager', 'System Manager', 'Administrator', 'Shift Manager']
    has_management_access = any(role in management_roles for role in user_roles)
    
    if not filters:
        filters = {}
    elif isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except (json.JSONDecodeError, TypeError, ValueError):
            filters = {}

    if employee_filters:
        if isinstance(employee_filters, str):
            try:
                employee_filters = json.loads(employee_filters)
            except (json.JSONDecodeError, TypeError, ValueError):
                employee_filters = {}
        filters.update(employee_filters)
        
    if shift_filters:
        if isinstance(shift_filters, str):
            try:
                shift_filters = json.loads(shift_filters)
            except (json.JSONDecodeError, TypeError, ValueError):
                shift_filters = {}
        filters.update(shift_filters)
    
    conditions = [
        "`tabShift Assignment`.docstatus < 2",
        "`tabShift Assignment`.status = 'Active'"
    ]
    
    values = {
        'start': start,
        'end': end
    }
    
    # Filter for employees - only show published shifts
    if not has_management_access:
        conditions.append("IFNULL(`tabShift Assignment`.custom_published, 0) = 1")
    
    if filters.get('company'):
        conditions.append("`tabShift Assignment`.company = %(company)s")
        values['company'] = filters.get('company')
        
    if filters.get('department'):
        conditions.append("`tabShift Assignment`.department = %(department)s")
        values['department'] = filters.get('department')
        
    if filters.get('designation'):
        conditions.append("`tabShift Assignment`.designation = %(designation)s")
        values['designation'] = filters.get('designation')
        
    if filters.get('employee'):
        conditions.append("`tabShift Assignment`.employee = %(employee)s")
        values['employee'] = filters.get('employee')
        
    if filters.get('shift_type'):
        conditions.append("`tabShift Assignment`.shift_type = %(shift_type)s")
        values['shift_type'] = filters.get('shift_type')
    
    where_clause = " AND ".join(conditions)
    
    try:
        # FIXED: Removed 'color' field that doesn't exist
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
                `tabShift Assignment`.department
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
        """, values, as_dict=True)
    except Exception as e:
        frappe.log_error(
            message=f"Roster Query Error: {str(e)}\nFilters: {filters}",
            title="Pro Coaching - Roster Query Failed"
        )
        return []
    
    events = []
    for shift in shifts:
        title = f"{shift.employee_name} ({shift.shift_type})"
        
        # Color coding: Green for published, Orange for unpublished
        if shift.custom_published:
            bg_color = '#28a745'  # Green
        else:
            bg_color = '#fd7e14'  # Orange

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
