app_name = "procoaching_custom_hr"
app_title = "Pro Coaching Custom HR"
app_publisher = "Pro Coaching"
app_description = "Custom HR modifications for roster filtering"
app_email = "info@pro-coaching.co.uk"
app_license = "MIT"

# Use ONLY hooks - no monkey-patching!
override_whitelisted_methods = {
    "hrms.api.roster.get_events": "procoaching_custom_hr.overrides.roster_override.get_events"
}
