__version__ = '0.0.1'

import frappe

def patch_roster_api():
    """
    Patch HRMS Roster API with custom filtering logic.
    This ensures the override works even if hooks fail.
    """
    try:
        import hrms.api.roster
        from procoaching_custom_hr.overrides.roster_override import get_events
        
        # Replace the default function with our custom one
        hrms.api.roster.get_events = get_events
        
        frappe.log_error(
            message="Successfully patched hrms.api.roster.get_events",
            title="Pro Coaching - Roster Patch Success"
        )
        
    except ImportError as e:
        frappe.log_error(
            message=f"Import Error: {str(e)}",
            title="Pro Coaching - Roster Patch Import Error"
        )
    except Exception as e:
        frappe.log_error(
            message=f"Failed to patch Roster API: {str(e)}",
            title="Pro Coaching - Roster Patch Error"
        )

# Execute patch on import
patch_roster_api()
