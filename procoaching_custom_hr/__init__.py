__version__ = '0.0.1'

import frappe

def patch_roster_api():
    """
    Patch HRMS Roster API with custom filtering logic.
    Employees see only published shifts, managers see all shifts.
    """
    try:
        import hrms.api.roster
        from procoaching_custom_hr.overrides.roster_override import get_events
        
        # Replace the default function with our custom one
        hrms.api.roster.get_events = get_events
        
    except Exception as e:
        # Log errors for debugging (don't crash the site)
        frappe.log_error(
            message=f"Failed to patch Roster API: {str(e)}\n\n{frappe.get_traceback()}",
            title="Pro Coaching - Roster Patch Error"
        )

# Apply patch on module import (safely)
try:
    patch_roster_api()
except:
    pass  # Fail silently, don't break the site
