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
        
        # REMOVED PRINT STATEMENTS to prevent job runner failures
        # frappe.logger().info("[Pro Coaching] Successfully patched hrms.api.roster.get_events") 

    except ImportError:
        # Fail silently or log to frappe.log (avoiding print)
        pass 
    except Exception as e:
        # Log error to error log instead of stdout
        # frappe.log_error(f"Failed to patch Roster API: {str(e)}", "Pro Coaching Patch Error")
        pass

# Run the patch immediately
patch_roster_api()
