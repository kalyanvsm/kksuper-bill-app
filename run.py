from kvsm_shop import app,db,socketio

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    socketio.run(app, debug=True)