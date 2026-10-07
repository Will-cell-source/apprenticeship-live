"""Send one test error to the Make scenario, to check error alerts work."""
import logging

import main

alerts = main.setup_logging()
if alerts is None:
    print("Error alerts are off: put your Make webhook address in .env first.")
else:
    logging.error("Test alert: if you got this email, error alerts work.")
    if alerts.failed:
        print("The test alert was NOT sent (see the message above).")
    else:
        print("Test alert sent to Make. Check your email in a minute.")
