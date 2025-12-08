__version__ = '0.0.1'

import frappe

def patch_roster_api():
    """
    NUCLEAR FIX: Manually swap the HRMS Roster function with our Custom function.
    This runs when the server starts, bypassing hooks.py limitations.
    """
    try:
        import hrms.api.roster
        from procoaching_custom_hr.overrides.roster_override import get_events
        hrms.api.roster.get_events = get_events
    except ImportError:
        pass
    except Exception as e:
        frappe.log_error(
            message=f"Failed to patch Roster API: {str(e)}",
            title="Pro Coaching - Roster Patch Error"
        )

patch_roster_api()
