@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    patient_id = data.get('patient_id')
    message = data.get('message')
    
    # Your existing chat logic here
    
    return jsonify({"response": "Your response here"}) 