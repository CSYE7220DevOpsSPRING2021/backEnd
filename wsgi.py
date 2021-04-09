# The wsgi.py file creates an application object (or callable) for the Gunicorn server
# so that the server can use it. Each time a request comes, the server uses this application 
# object to run the application’s request handlers upon parsing the URL.

from main import app

if __name__ == "__main__":
  app.run()