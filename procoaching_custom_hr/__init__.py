# Improved version with better error handling
__version__ = '0.0.1'

import frappe

def patch_roster_api():
    """
    NUCLEAR FIX: Manually swap the HRMS Roster function with our Custom function.
    This runs when the server starts, bypassing hooks.py limitations.
    """
    try:
        # 1. Import the original API module
        import hrms.api.roster
        
        # 2. Import YOUR custom override function
        from procoaching_custom_hr.overrides.roster_override import get_events
        
        # 3. Force the swap
        # This tells the server: "Whenever someone asks for hrms.api.roster.get_events, give them MINE instead."
        hrms.api.roster.get_events = get_events
        
        # Removed print statements as they cause agent job issues
        
    except ImportError:
        # HRMS app might not be installed yet - this is okay during initial setup
        pass
    except Exception as e:
        # Log error to Frappe's error log instead of printing
        frappe.log_error(
            message=f"Failed to patch Roster API: {str(e)}",
            title="Pro Coaching - Roster Patch Error"
        )

# Run the patch immediately
patch_roster_api()
