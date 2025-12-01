app_name = "procoaching_custom_hr"
app_title = "Pro Coaching Custom HR"
app_publisher = "Pro Coaching"
app_description = "Custom HR modifications for roster filtering"
app_email = "info@pro-coaching.co.uk"
app_license = "MIT"


# CRITICAL: Override the standard Shift Assignment event fetching
# This ensures we intercept the data before it reaches the calendar/roster.
override_whitelisted_methods = {
    "hrms.hr.doctype.shift_assignment.shift_assignment.get_events": "procoaching_custom_hr.overrides.roster_override.get_events"
}
