"""Send one test error email, to check the email settings in .env work."""
import logging

import main

email = main.setup_logging()
if email is None:
    print("Error emails are off: fill in every setting in .env first.")
else:
    logging.error("Test alert: if you got this email, error emails work.")
    if email.failed:
        print("The test email was NOT sent (see the message above).")
    else:
        print("Test email sent. Check your inbox (and spam) in a minute.")
