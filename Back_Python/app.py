from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from Prompt_Completion_V00 import Preguntas
import random
import os
import json
import io

app = Flask(__name__, static_folder='react_build')
cors = CORS(app)

History = [[
        {
            "id": 0,
            "responseChatbot": "Quiz n°1"
        },
        {
            "id": 1,
            "responseChatbot": "Usted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó.\nPor favor sientase con toda la confianza de responder las preguntas según sus conocimientos y sin presiones de ningún tipo.\nLos resultados que obtenga serán utilizados para refinar nuestro algoritmo de recomendación de ejercicios.\n\nAtentamente: Equipo de Pensando Problemas."
        }
    ]]
history_path = "react_build/"

# Variables for the sake of the program
record = []
n = 0
inicializador_id = 1
info = {}
success_fail = True

k = 140
emph = '#'+'-'*k+'#'

# Retrieve the history and save it in local when launching the app
def load_history():
    global History
    global inicializador_id
    file_path = history_path+"History.json"

    inicializador_id = 1 # Cambiar o añadir una función acá para instanciar el inicializador con lo que uno quiera
    if os.path.exists(file_path):
        if len(History[0])<3:
            History[0].append({'id':2, 'responseChatbot': call_image(inicializador_id)}) # Cambiar el inicializador permite cambiar la primera imagen que se muestra
        with io.open(os.path.join(history_path, 'History.json'), 'w', encoding='utf-8') as history_file:
            history_file.write(json.dumps(History))
    else:
        with io.open(os.path.join(history_path, 'History.json'), 'w') as history_file:
            history_file.write(json.dumps([[]]))


def ask_message():
    ask_msg = input('\n\nEscriba su respuesta: ')
    return ask_msg

def fail_message():
    fail_msg = '\n\nSe ha equivocado en la elección de la respuesta correcta. A continuación se le mostrará un ejercicio de nivel menor o igual al que realizó. ¿ Desea Continuar ?\n\n'
    return(fail_msg)

def success_message():
    success_msg = '\n\nHa acertado en la elección de la respuesta correcta. A continuación se le mostrará un ejercicio de nivel superior o igual al que realizó. ¿ Desea Continuar ?\n\n'
    return(success_msg)

def call_image(id): 
    img = 'react_build/Images/Preg_0{}.png'.format(id)
    print("Image", img)
    return img

def call_question(id):
    return Preguntas[id]

def update_question(success_fail,inicializador_id):
    global info
    indices = []
    dificultad_actual = Preguntas[inicializador_id]['dif']
    for pregunta in Preguntas:
        if pregunta != inicializador_id:
            if success_fail:
                if info['dif']>= dificultad_actual:
                    indices.append(pregunta)
            else:
                if info['dif']<= dificultad_actual:
                    indices.append(pregunta)
    try:
        indice = random.choice(indices)
        return indice
    except:
        print('\nNo hay más ejercicios para que usted resuelva.\n')


@app.route('/api/query', methods=['POST'])
def receive_question():
    global inicializador_id
    global record
    global info
    global success_fail
    try:
        data = request.get_json()
        responseStudent = data.get('responseStudent')
        # Verify that the question isn't empty
        if len(responseStudent)==0 or responseStudent.isspace():
            return jsonify({'error': 'La pregunta esta vacia'}), 204
        
        # Retrieve the history stored in the front
        history = data.get('history')
        if history is None:
            history=[]
        if len(responseStudent)==0:
            responseStudent.append(" ")
        if len(history)==0:
            q_id = 0
        else:
            q_id = history[-1]['id']
        question = history[-1]['responseChatbot']
        if "¿ Desea Continuar ?" in question:
            if ("si" in responseStudent) or ("yes" in responseStudent):
                inicializador_id = update_question(success_fail,inicializador_id) # Se actualiza a una nueva pregunta para que el estudiante resuelva.
                responseChatbot = call_image(inicializador_id)
            elif ("no" in responseStudent):
                responseChatbot = "bye"
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea Continuar ?"
            response = {
                    'id': q_id,
                    'responseStudent': f"{responseStudent}",
                    'responseChatbot': f"{responseChatbot}"
                }
                

        else:
            info = call_question(inicializador_id)
            success_fail = responseStudent in info['res'] # Revisa si la respuesta es correcta o no.
            
            record.append((inicializador_id,success_fail))
            if success_fail:
                responseChatbot = success_message() # Mensaje de acierto en la respuesta
            else:
                responseChatbot = fail_message() # Mensaje de fallo en la respuesta:


            response = {
                'id': q_id,
                'responseStudent': f"{responseStudent}",
                'responseChatbot': f"{responseChatbot}"
            }
        
        return jsonify({'message': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    load_history()
    app.run(port=3001, debug=True) 