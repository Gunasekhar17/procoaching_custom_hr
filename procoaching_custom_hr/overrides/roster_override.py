import frappe
from frappe import _

# Import the original HRMS function to reuse its logic
from hrms.api.roster import get_events as hrms_get_events

@frappe.whitelist()
def get_events(start=None, end=None, month_start=None, month_end=None, filters=None, employee_filters=None, shift_filters=None):
   
    
    # Get the standard HRMS events first
    # IMPORTANT: HRMS returns a DICT grouped by employee_id, NOT a flat list!
    # Structure: {"HR-EMP-00164": [{event}, {event}], "HR-EMP-00165": [{event}]}
    # Build kwargs dict, only including non-None values to satisfy type validation
    kwargs = {}
    if start is not None:
        kwargs['start'] = start
    if end is not None:
        kwargs['end'] = end
    if month_start is not None:
        kwargs['month_start'] = month_start
    if month_end is not None:
        kwargs['month_end'] = month_end
    if filters is not None:
        kwargs['filters'] = filters
    if employee_filters is not None:
        kwargs['employee_filters'] = employee_filters
    if shift_filters is not None:
        kwargs['shift_filters'] = shift_filters
    
    events = hrms_get_events(**kwargs)
    
    # Check if user has management access
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    management_roles = ['HR Manager', 'System Manager', 'Administrator', 'Shift Manager']
    has_management_access = any(role in management_roles for role in user_roles)
    
    # If user is management, return all events as-is (grouped dict)
    if has_management_access:
        return events
    
    # For non-management users, filter by custom_published
    if not events or not isinstance(events, dict):
        return events
    
    # Collect all shift names from all employees to query in one go
    all_shift_names = []
    for employee_id, employee_events in events.items():
        if isinstance(employee_events, list):
            for event in employee_events:
                if event.get('name'):
                    all_shift_names.append(event.get('name'))
    
    if not all_shift_names:
        return events
    
    # Query which shifts are published (single DB call for efficiency)
    published_shifts = frappe.db.get_all(
        'Shift Assignment',
        filters={
            'name': ['in', all_shift_names],
            'custom_published': 1
        },
        pluck='name'
    )
    
    # Convert to set for O(1) lookup
    published_set = set(published_shifts)
    
    # Filter each employee's events, maintaining the grouped structure
    filtered_events = {}
    for employee_id, employee_events in events.items():
        if isinstance(employee_events, list):
            # Filter this employee's shifts to only published ones
            filtered_employee_events = [
                event for event in employee_events
                if event.get('name') in published_set
            ]
            # Keep employee in response even if no published shifts (empty array)
            # This ensures employee row still appears in roster UI
            filtered_events[employee_id] = filtered_employee_events
    
    return filtered_events
