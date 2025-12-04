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
        print("[Pro Coaching] Successfully patched hrms.api.roster.get_events")
        
    except ImportError:
        print("[Pro Coaching] Could not patch Roster API - HRMS app might not be installed yet.")
    except Exception as e:
        print(f"[Pro Coaching] Failed to patch Roster API: {str(e)}")

# Run the patch immediately
patch_roster_api()
