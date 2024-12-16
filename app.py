from flask import Flask, jsonify, request
import calendarService

app = Flask(__name__)

# Endpoint to get all books
@app.route('/calendar/events/<int:year>', methods=['GET'])
def getCalendarEventsYear(year):
    events = calendarService.countCalendarEventsYear("Palestra", year)
    return jsonify({'event_count': events})

if __name__ == '__main__':
    app.run(debug=True)