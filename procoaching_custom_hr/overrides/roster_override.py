import frappe
from frappe import _
from hrms.api.roster import get_events as hrms_get_events

@frappe.whitelist()
def get_events(start=None, end=None, month_start=None, month_end=None, filters=None, employee_filters=None, shift_filters=None):
    
    # 1. Setup Arguments
    kwargs = {}
    if start is not None: kwargs['start'] = start
    if end is not None: kwargs['end'] = end
    if month_start is not None: kwargs['month_start'] = month_start
    if month_end is not None: kwargs['month_end'] = month_end
    if filters is not None: kwargs['filters'] = filters
    if employee_filters is not None: kwargs['employee_filters'] = employee_filters
    if shift_filters is not None: kwargs['shift_filters'] = shift_filters
    
    # 2. Fetch Standard Events
    events = hrms_get_events(**kwargs)
    
    if not events or not isinstance(events, dict):
        return events
    
    # 3. Check Permissions
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    management_roles = ['HR Manager', 'System Manager', 'Administrator', 'Shift Manager']
    has_management_access = any(role in management_roles for role in user_roles)
    
    # 4. Filtering Logic (Only for Non-Management)
    if not has_management_access:
        all_shift_names = []
        for employee_id, employee_events in events.items():
            if isinstance(employee_events, list):
                for event in employee_events:
                    if event.get('name'):
                        all_shift_names.append(event.get('name'))
        
        if all_shift_names:
            published_shifts = frappe.db.get_all(
                'Shift Assignment',
                filters={
                    'name': ['in', all_shift_names],
                    'custom_published': 1
                },
                pluck='name'
            )
            
            published_set = set(published_shifts)
            
            filtered_events = {}
            for employee_id, employee_events in events.items():
                if isinstance(employee_events, list):
                    filtered_employee_events = [
                        event for event in employee_events
                        if event.get('name') in published_set
                    ]
                    filtered_events[employee_id] = filtered_employee_events
            
            # Update main events variable with the filtered list
            events = filtered_events

    # 5. Icon Logic (Applies to EVERYONE - Managers & Employees)
    employee_ids = list(events.keys())
    
    if employee_ids:
        # Fetch data using your specific field names
        emp_data = frappe.db.get_all(
            'Employee', 
            filters={'name': ['in', employee_ids]}, 
            fields=[
                'name',
                'custom_has_first_aid',
                'custom_has_safeguarding_certificate', 
                'custom_has_dbs',
                'custom_has_food_hygiene'
            ]
        )
        
        icon_map = {}
        for emp in emp_data:
            icons = ""
            
            # Helper to check for "Yes", "yes", "1", "True"
            def is_yes(val):
                return str(val).strip().lower() in ['yes', '1', 'true']

            if is_yes(emp.get('custom_has_first_aid')):
                icons += "⛑️ "
            
            if is_yes(emp.get('custom_has_safeguarding_certificate')):
                icons += "🛡️ "
            
            if is_yes(emp.get('custom_has_dbs')):
                icons += "👮 "
            
            if is_yes(emp.get('custom_has_food_hygiene')):
                icons += "🍽️ "
            
            icon_map[emp['name']] = icons.strip()
        
        # Apply icons to existing 'shift_type' field
        for employee_id, event_list in events.items():
            emp_icons = icon_map.get(employee_id, "")
            
            if emp_icons and isinstance(event_list, list):
                for event in event_list:
                    # Check if shift_type exists before modifying it
                    if event.get('shift_type'):
                        # Prepend icons to the existing shift_type string
                        event['shift_type'] = f"{emp_icons} {event['shift_type']}"

    return events
