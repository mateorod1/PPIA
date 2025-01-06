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
            "responseChatbot": "Usted iniciará la práctica libre de ejercicios que el equipo pedagógico de Pensando Problemas preparó.\nPor favor sientase con toda la confianza de responder las preguntas según sus conocimientos y sin presiones de ningún tipo.\nLos resultados que obtenga serán utilizados para refinar nuestro algoritmo de recomendación de ejercicios.\n\nAtentamente: Equipo de Pensando Problemas."
        }
    ]]
history_path = "react_build/"

# Variables for the sake of the program
record = []
inicializador_id = 1
info = {}
success_fail = True
selected_theme = None

k = 140

def retrieve_temas_dif():
    temas = []
    difs = []
    for preg in Preguntas:
        if Preguntas[preg]['tema'] not in temas:
            temas.append(Preguntas[preg]['tema'])
        if Preguntas[preg]['dif'] not in difs:
            difs.append(Preguntas[preg]['dif'])

    return(temas, difs)

# Retrieve the history and save it in local when launching the app
def load_history():
    global History
    global inicializador_id
    file_path = history_path+"History.json"

    (temas, difs) = retrieve_temas_dif()
    temas_str = "\t\t- "+",\n\t\t- ".join(map(str, temas))  # For string lists
    difs_str = "\t\t- "+", ".join(map(str, difs))  # For numeric lists, convert each item to a string

    list_temas_difs = f'''Eliges un tema y una dificultad dentro de la lista para empezar el quiz:  \n                                 
        Temas: \n{temas_str}\n
        Dificultades: \n{difs_str}

Tu respuesta deber ser formatada como lo siguiente: 
tema dificultad (ej: logica 2)'''
    
    inicializador_id = 1 # Cambiar o añadir una función acá para instanciar el inicializador con lo que uno quiera
    if os.path.exists(file_path):
        History[0].append({'id':1, 'responseChatbot': list_temas_difs})
        with io.open(os.path.join(history_path, 'History.json'), 'w', encoding='utf-8') as history_file:
            history_file.write(json.dumps(History))
    else:
        with io.open(os.path.join(history_path, 'History.json'), 'w') as history_file:
            history_file.write(json.dumps([[]]))


def ask_message():
    ask_msg = input('Escriba su respuesta: ')
    return ask_msg

def fail_message():
    fail_msg = 'Se ha equivocado en la elección de la respuesta correcta. A continuación se le mostrará un ejercicio de nivel menor o igual al que realizó. ¿ Desea Continuar ?'
    return(fail_msg)

def success_message():
    success_msg = 'Ha acertado en la elección de la respuesta correcta. A continuación se le mostrará un ejercicio de nivel superior o igual al que realizó. ¿ Desea Continuar ?'
    return(success_msg)

def tail_message():
    global record
    themes = []
    difs_succeed = {}
    difs_failed = {}
    print(record)
    if len(record)==0:
        return 'Ha finalizado la práctica.\nUsted realizó {} ejercicios.\n\n'.format(len(record)) + '\n¿ Desea reiniciar un quiz ?'
    for rec in record:
        if Preguntas[rec[0]]['tema'] not in themes:
            themes.append(Preguntas[rec[0]]['tema'])
        if rec[1]:
            if Preguntas[rec[0]]['dif'] in difs_succeed:
                difs_succeed[Preguntas[rec[0]]['dif']]+=1
            else:
                difs_succeed[Preguntas[rec[0]]['dif']] = 1
        else:
            if Preguntas[rec[0]]['dif'] in difs_failed:
                difs_failed[Preguntas[rec[0]]['dif']]+=1
            else:
                difs_failed[Preguntas[rec[0]]['dif']] = 1

    temas_str = ", ".join(map(str, themes))
    
    sorted_dict_succeed = dict(sorted(difs_succeed.items()))
    summary_succeed = "\n ".join(
        f"\t- {count} preguntas{'s' if count > 1 else ''} del nivel {level} logradas"
        for level, count in sorted_dict_succeed.items()
    )
    sorted_dict_failed = dict(sorted(difs_failed.items()))
    summary_failed = "\n ".join(
        f"\t- {count} preguntas{'s' if count > 1 else ''} del nivel {level} perdidas"
        for level, count in sorted_dict_failed.items()
    )
    summary = summary_succeed + "\n\n" + summary_failed

    rec_str = f"El resumen de la practica es el siguiente: \n{summary}"
    
    tail_message = 'Ha finalizado la práctica.\nUsted realizó {} ejercicios.\n\n'.format(len(record)) + "El tema elegido fue "+temas_str+".\n"+ rec_str + '\n¿ Desea reiniciar un quiz ?'
    return(tail_message)

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
                responseChatbot = tail_message()
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea Continuar ?"
            response = {
                    'id': q_id,
                    'responseStudent': f"{responseStudent}",
                    'responseChatbot': f"{responseChatbot}"
                }
                
        elif "Eliges un tema y una dificultad dentro de la lista para empezar el quiz:" in question:
            (temas, difs) = retrieve_temas_dif()
            global selected_theme
            selected_dif = None
            for tema in temas:
                if tema in responseStudent:
                    selected_theme = tema
                    break
            for dif in difs:
                if str(dif) in responseStudent:
                    selected_dif = dif
                    break
            if selected_theme is None or selected_dif is None:
                temas_str = "\t\t- "+",\n\t\t- ".join(map(str, temas))  # For string lists
                difs_str = "\t\t- "+", ".join(map(str, difs))  # For numeric lists, convert each item to a string

                list_temas_difs = f'''Eliges un tema y una dificultad dentro de la lista para empezar el quiz:  \n                                 
        Temas: \n{temas_str}\n
        Dificultades: \n{difs_str}

Tu respuesta deber ser formatada como lo siguiente: 
tema dificultad (ej: logica 2)'''
                
                responseChatbot = 'No entendí tu respuesta.\n'+ list_temas_difs
            
            else:
                
                ### Crear la funcion que permite elegir la pregunta segun el tema y la dificultad elegida
                #   - cambiar la funcion update_question para que toma en cuenta un tema dado (y eso para toda la sesión)
                #   - crear una función que eliga la primera pregunta de la sesión porque toma en cuenta la dificultad
                #   - o hacer los dos en una unica función 
                # Esta funcion update inicializador_id estilo:
                #       inicializador_id = update_question(selected_theme, selected_dif)

                responseChatbot = call_image(inicializador_id)

            # Respuesta final
            response = {
                'id': q_id,
                'responseStudent': f"{responseStudent}",
                'responseChatbot': f"{responseChatbot}"
            }
    
        elif "¿ Desea reiniciar un quiz ?" in question:
            if 'si' in responseStudent or 'yes' in responseStudent:
                record = []
                responseChatbot = 'reinit'
            elif ("no" in responseStudent):
                responseChatbot = tail_message()
            else:
                responseChatbot = "No entendí tu respuesta. ¿ Desea reiniciar un quiz ?"
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