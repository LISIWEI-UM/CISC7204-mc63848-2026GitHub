"""Lab04 practice: renamed entry point and updated title (35 px)."""
from flight_delay import create_app
app=create_app(practice=True)
if __name__=='__main__':
    print('Five-output year callback; stop with Ctrl+C',flush=True)
    app.run(host='127.0.0.1',port=8055,debug=False)
