import os
import dotenv

dotenv.load_dotenv()

TOKEN = os.getenv("TG_TOKEN")
script_file = ["script0.qs", "script1.qs", "script2.qs", "script3.qs", "script4.qs"]
admins = [6505930340, 517953164]
