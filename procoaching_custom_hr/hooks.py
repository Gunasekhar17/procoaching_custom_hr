app_name = "procoaching_custom_hr"
app_title = "Pro Coaching Custom HR"
app_publisher = "Pro Coaching"
app_description = "Custom HR modifications for roster filtering"
app_email = "info@pro-coaching.co.uk"
app_license = "MIT"

# ... (Keep existing comments/includes if you have them) ...

# CRITICAL: Override ALL event fetching methods.
# The previous version failed because the Roster Page uses the 'api' path, 
# not just the 'doctype' path. We must override ALL of them.

override_whitelisted_methods = {
    # 1. Standard Shift Assignment Logic (Backend)
    "hrms.hr.doctype.shift_assignment.shift_assignment.get_events": "procoaching_custom_hr.overrides.roster_override.get_events",
    
    # 2. Legacy Roster Page Logic
    "hrms.hr.page.roster.roster.get_events": "procoaching_custom_hr.overrides.roster_override.get_events",
    
    # 3. Modern Roster API (THE FIX: This is what your screenshot showed)
    "hrms.api.roster.get_events": "procoaching_custom_hr.overrides.roster_override.get_events"
}
