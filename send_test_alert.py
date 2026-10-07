"""Send one test error email, to check the email settings in .env work."""
import logging

import main

if main.setup_logging():
    logging.error("Test alert: if you got this email, error emails work.")
    print("Test error sent. Check your inbox (and spam) in a minute.")
else:
    print("Error emails are off: fill in every setting in .env first.")
