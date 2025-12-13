import frappe
from frappe import _
import json

@frappe.whitelist()
def get_events(start=None, end=None, month_start=None, month_end=None, filters=None, employee_filters=None, shift_filters=None):
   
    
    try:
        # --- 1. Handle date parameters ---
        if not start and month_start:
            start = month_start
        if not end and month_end:
            end = month_end
        
        if not start or not end:
            return []

        # Convert to string if datetime objects
        start = str(start) if start else None
        end = str(end) if end else None

        if not start or not end:
            return []

        # --- 2. Parse filters (Robust parsing) ---
        filters = _parse_json_filter(filters) or {}
        employee_filters = _parse_json_filter(employee_filters) or {}
        shift_filters = _parse_json_filter(shift_filters) or {}
        
        # Merge all filters
        filters.update(employee_filters)
        filters.update(shift_filters)

        # --- 3. Build SQL Conditions ---
        conditions = [
            "`tabShift Assignment`.docstatus < 2",
            "`tabShift Assignment`.status = 'Active'"
        ]
        values = {'start': start, 'end': end}

        # Check user permissions
        user = frappe.session.user
        user_roles = frappe.get_roles(user)
        management_roles = ['HR Manager', 'System Manager', 'Administrator', 'Shift Manager']
        has_management_access = any(role in management_roles for role in user_roles)

        # Non-management users can only see published shifts
        if not has_management_access:
            conditions.append("IFNULL(`tabShift Assignment`.custom_published, 0) = 1")

        # Dynamic filters
        for field in ['company', 'department', 'employee', 'shift_type']:
            if filters.get(field):
                conditions.append(f"`tabShift Assignment`.{field} = %({field})s")
                values[field] = filters.get(field)

        where_clause = " AND ".join(conditions)

        # --- 4. Execute Query with Error Handling ---
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
                    `tabShift Assignment`.company,
                    `tabShift Assignment`.department,
                    `tabShift Assignment`.shift_location
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
                f"Roster Query Error: {str(e)}\n\nFilters: {filters}\n\nSQL: {where_clause}",
                "Pro Coaching Roster Error"
            )
            return []

        if not shifts:
            return []

        # --- 5. Get Shift Type Colors (with error handling) ---
        shift_colors = _get_shift_colors(shifts)

        # --- 6. FORMAT RESPONSE - CLEAN DATA WITH DEFAULTS ---
        events = []
        
        for shift in shifts:
            # Validate and convert dates
            try:
                start_date = str(shift.get('start_date', '')) or ''
                end_date = str(shift.get('end_date', '')) or ''
            except Exception as e:
                frappe.log_error(f"Date conversion error: {str(e)}", "Pro Coaching Roster")
                continue

            # Get shift color with fallback
            shift_type = shift.get('shift_type') or 'Default'
            color = shift_colors.get(shift_type, '#3788d8')

            # Create CLEAN event object with all required fields and defaults
            event = {
                # Required identifier fields
                'name': shift.get('name') or '',
                'id': shift.get('name') or '',
                
                # Display fields
                'title': f"{shift.get('employee_name', 'Unknown')} ({shift.get('shift_type', 'No Shift')})",
                'subject': f"{shift.get('employee_name', 'Unknown')} ({shift.get('shift_type', 'No Shift')})",
                
                # Data fields
                'employee': shift.get('employee') or '',
                'employee_name': shift.get('employee_name') or 'Unknown',
                'shift_type': shift_type,
                'shift_location': shift.get('shift_location') or '',
                'department': shift.get('department') or '',
                'company': shift.get('company') or '',
                
                # Date fields (ALWAYS strings)
                'start': start_date,
                'end': end_date,
                
                # Display properties
                'allDay': True,
                'doctype': 'Shift Assignment',
                
                # Status and styling
                'status': shift.get('status') or 'Active',
                'color': color
            }
            
            # Only add if we have minimum required fields
            if event['name'] and event['start'] and event['end']:
                events.append(event)

        frappe.logger().info(f"[Pro Coaching Roster] Returning {len(events)} events")
        return events

    except Exception as e:
        frappe.log_error(
            f"Unexpected error in get_events: {str(e)}",
            "Pro Coaching Roster Error"
        )
        return []


def _parse_json_filter(filter_str):
    """
    Safely parse JSON filter string
    Returns dict or None
    """
    if not filter_str:
        return None
    
    if isinstance(filter_str, dict):
        return filter_str
    
    if isinstance(filter_str, str):
        try:
            return json.loads(filter_str)
        except json.JSONDecodeError:
            frappe.logger().warning(f"Invalid JSON filter: {filter_str}")
            return None
    
    return None


def _get_shift_colors(shifts):
    """
    Fetch shift type colors efficiently
    Returns dict: {shift_type_name: color_code}
    """
    if not shifts:
        return {}
    
    try:
        # Get unique shift types
        shift_types = list(set([s.get('shift_type') for s in shifts if s.get('shift_type')]))
        
        if not shift_types:
            return {}
        
        # Fetch colors from Shift Type
        colors = frappe.db.get_all(
            'Shift Type',
            filters={'name': ['in', shift_types]},
            fields=['name', 'color']
        )
        
        # Build color map with defaults
        shift_colors = {}
        for color_obj in colors:
            if color_obj.get('color'):
                shift_colors[color_obj['name']] = color_obj['color']
        
        return shift_colors
    
    except Exception as e:
        frappe.logger().warning(f"Error fetching shift colors: {str(e)}")
        return {}
