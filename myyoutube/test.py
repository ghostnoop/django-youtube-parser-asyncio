import os

from dotenv import load_dotenv

a=os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../.env'))
print(a)
load_dotenv(dotenv_path=a)
print(os.getenv('secret'))
