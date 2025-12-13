// Guard against HRMS roster onError handler that assumes O.messages[0]
(function () {
    const original_call = frappe.call;

    frappe.call = function (opts) {
        const error_handler = opts.error;

        if (typeof error_handler === "function") {
            opts.error = function (O) {
                // Ensure O and O.messages are safe
                if (!O) {
                    O = {};
                }
                if (!Array.isArray(O.messages)) {
                    O.messages = [];
                }
                return error_handler(O);
            };
        }

        return original_call.call(this, opts);
    };
})();
