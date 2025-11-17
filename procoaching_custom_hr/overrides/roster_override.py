import frappe
from frappe import _
import json

@frappe.whitelist()
def get_events(start, end, filters=None):
    """
    Custom roster get_events with:
    1. Publication status filtering (employees see only published, managers see all)
    2. Training icons display (First Aid, Safeguarding, DBS)
    3. Document indicators (Briefing, Risk Assessment)
    """
    
    # Get current user and roles
    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    management_roles = ['HR Manager', 'System Manager', 'Administrator', 'HR User']
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
    
    # CRITICAL: Publication filter for non-managers
    if not has_management_access:
        conditions.append("`tabShift Assignment`.custom_published = 1")
        frappe.logger().info(f"Roster: Employee {user} - showing only published shifts")
    else:
        frappe.logger().info(f"Roster: Manager {user} - showing all shifts")
    
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
    
    # Fetch shifts with employee training data and documents
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
            `tabShift Assignment`.custom_briefing_document,
            `tabShift Assignment`.custom_risk_assessment,
            `tabEmployee`.custom_first_aider,
            `tabEmployee`.custom_safeguarding,
            `tabEmployee`.custom_dbs_checked
        FROM 
            `tabShift Assignment`
        LEFT JOIN
            `tabEmployee` ON `tabShift Assignment`.employee = `tabEmployee`.name
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
    
    frappe.logger().info(f"Roster: Found {len(shifts)} shifts for user {user}")
    
    # Format events for calendar display with training icons and document indicators
    events = []
    for shift in shifts:
        # Build training badges
        badges = []
        if shift.get('custom_first_aider'):
            badges.append('🩹')  # First Aid
        if shift.get('custom_safeguarding'):
            badges.append('🛡️')  # Safeguarding
        if shift.get('custom_dbs_checked'):
            badges.append('✓')   # DBS
        
        badges_html = ' '.join(badges)
        
        # Build document indicators
        doc_indicators = []
        if shift.get('custom_briefing_document'):
            doc_indicators.append('📋')  # Briefing
        if shift.get('custom_risk_assessment'):
            doc_indicators.append('⚠️')   # Risk Assessment
        
        doc_html = ' '.join(doc_indicators)
        
        # Combine title with all indicators
        title_parts = [shift.employee_name]
        if badges_html:
            title_parts.append(badges_html)
        if doc_html:
            title_parts.append(doc_html)
        
        title = ' '.join(title_parts)
        
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
            # Color: Green for published, Orange for unpublished
            'backgroundColor': '#10b981' if shift.custom_published else '#f59e0b',
            'borderColor': '#10b981' if shift.custom_published else '#f59e0b',
            'textColor': '#ffffff'
        }
        events.append(event)
    
    return events
