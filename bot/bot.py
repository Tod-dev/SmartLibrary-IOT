import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from config import BOTKEY,SERVER_URL
import requests
from datetime import datetime
import json
from setupMqtt import ClientMQTT

#LOGGING
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def getOperations():
    return ['prenota','ritira','consegna']

#COMANDI
def start(update, context):
    """Send a message when the command /now is issued."""
    username = update.message.chat.username
    update.message.reply_text('Hello, {}!\n/help for documentation.'.format(username))

def help(update, context):
    """Send a message when the command /now is issued."""
    operazioniDesc = map(lambda x: '/{} , {} un libro.'.format(x,x), getOperations())
    text = '\n'.join(operazioniDesc)
    update.message.reply_text(text)

#TODO
def prenota(update, context):
    """Send a message when the command /now is issued."""
    print(update.message.text)
    #r = requests.get('{}/totems?nomeLibro={}'.format(SERVER_URL,nome))
    msg = update.message.text.split('/prenota ')
    if len(msg) == 1:
        #ho solo la scritta /prenota
        update.message.reply_text("Per prenotare un libro scrivi /prenota seguito dal nome del libro che desideri")
    else:
        #ho anche il nome del libro
        libro = msg[1]  #SECONDO ME BISOGNA METTERLO LOWER (msg[1].lower()) PER RENDERE PIU' FACILE LA RICERCA DEL LIBRO
        
        r = requests.get('{}/totems?nomeLibro={}'.format(SERVER_URL, libro))
        print(r.text)
        if r.text == '[]':
            update.message.reply_text('Spiacenti, ma il libro {} non è disponibile al momento'.format(libro))
            return
        
        r = json.loads(r.text)[0]
        idLibro = r['id']
        update.message.reply_text('Stai prenotando il libro: '+libro)

        #CREAZIONE CODICE DI PRENOTAZIONE E DISPLAY ALL'UTENTE
        d = dict()
        d["utente"] = 2
        d["libro"] = idLibro
        #d = json.dumps(d)
        print(d)
        r = requests.post(url=SERVER_URL+"/prenotazioni", json=d)
        print(r.text)

        #PUBLISH MQTT AL TOTEM CHE CONTIENE QUEL LIBRO
        mqttMessage = "IDSCOMPARTIMENTO/CODICE/IDPRENOTAZIONE"
        idTotem = 1
        mqttClient.publishMQTT(mqttMessage, idTotem)

    

#TODO
def ritira(update, context):
    """Send a message when the command /now is issued."""
    update.message.reply_text('Not yet implemented :(')
#TODO
def consegna(update, context):
    """Send a message when the command /now is issued."""
    update.message.reply_text('Not yet implemented :(')

#START BOT
def startBot():
    global updater
    """Start the bot."""
    updater = Updater(BOTKEY, use_context=True)
    dp = updater.dispatcher

    #HANDLERS COMANDI
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("prenota", prenota))
    dp.add_handler(CommandHandler("ritira", ritira))
    dp.add_handler(CommandHandler("consegna", consegna))
    
    updater.start_polling()
    return updater

#MAIN
if __name__ == '__main__':
    updater = startBot()
    updater.idle()