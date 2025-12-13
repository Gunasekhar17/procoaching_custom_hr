// Guard against HRMS roster onError handler bug that assumes O.messages[0] exists
(function() {
    const original_call = frappe.call;

    // Use "...args" to capture ALL arguments (method, args, callback, etc.)
    frappe.call = function(...args) {
        
        // 1. Identify if the first argument is the options object (Modern style)
        // e.g. frappe.call({ method: '...', error: ... })
        if (args.length > 0 && typeof args[0] === 'object' && args[0] !== null) {
            let opts = args[0];
            const original_error = opts.error;

            // Only wrap if there is an error handler defined
            if (typeof original_error === 'function') {
                opts.error = function(O) {
                    // Safety checks
                    if (!O) O = {};
                    if (!Array.isArray(O.messages)) {
                        O.messages = [];
                    }
                    return original_error(O);
                };
            }
        }

        // 2. Pass ALL arguments exactly as they were received
        return original_call.apply(this, args);
    };
})();
