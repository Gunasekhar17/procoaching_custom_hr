app_name = "procoaching_custom_hr"
app_title = "Pro Coaching Custom HR"
app_publisher = "Pro Coaching"
app_description = "Custom HR modifications for roster filtering"
app_email = "info@pro-coaching.co.uk"
app_license = "MIT"

# Include JS guard to prevent roster onError crash
app_include_js = [
    "/assets/procoaching_custom_hr/js/roster_error_guard.js"
]

override_whitelisted_methods = {
    "hrms.api.roster.get_events": "procoaching_custom_hr.overrides.roster_override.get_events"
}
