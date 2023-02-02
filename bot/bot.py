import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from config import BOTKEY,SERVER_URL
import requests
from datetime import datetime
import json
from PIL import Image
from io import BytesIO
#from setupMqtt import ClientMQTT

#LOGGING
logging.basicConfig(level=logging.DEBUG,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def getOperations():
    return ['prenota','consegna']

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
        return update.message.reply_text("Per prenotare un libro scrivi /prenota seguito dal nome del libro che desideri")
        
    try:

        #ho anche il nome del libro
        libro = msg[1]  #SECONDO ME BISOGNA METTERLO LOWER (msg[1].lower()) PER RENDERE PIU' FACILE LA RICERCA DEL LIBRO
        
        r = requests.get('{}/totems?nomeLibro={}'.format(SERVER_URL, libro))
        print(r.text)
        if r.text == '[]':
            update.message.reply_text('Spiacenti, ma il libro {} non è disponibile al momento'.format(libro))
            return
        
        r = json.loads(r.text)[0]
        idLibro = r['libro_id']

        #CREAZIONE CODICE DI PRENOTAZIONE E DISPLAY ALL'UTENTE
        d = dict()
        d["utente"] = update.message.chat.username
        d["libro_id"] = idLibro
        d["scompartimento_id"] = r['scompartimento_id']
        d["totem_id"] = r['totem_id']
        img = r["img"]
        #d = json.dumps(d)
        print(d)
        r = requests.post(url=SERVER_URL+"/prenotazioni", json=d)
        r = json.loads(r.text) 
        update.message.reply_text(r["descrizione"], parse_mode='HTML')
        if img != "":
            url = img
            response = requests.get(url)    
            update.message.reply_photo(photo=BytesIO(response.content))
    except Exception as e:
        print("ERRORE: {}".format(e))
        update.message.reply_text("Errore nel reperimento del libro")

#TODO
def consegna(update, context):
    """Send a message when the command /now is issued."""
    print(update.message.text)
    #RITORNARE LA LISTA DI TOTEM CON ALMENO UNO SCOMPARTIMENTO LIBERO
    try:
        r = requests.get('{}/totems/scompartimentolibero'.format(SERVER_URL))
        print(r.text)
        if r.text == '[]':
            update.message.reply_text('Spiacenti, ma non ci sono totem liberi al momento')
            return
        
        r = json.loads(r.text)
        #print(r)
        descrizione = 'Ecco l\'elenco dei totem liberi, puoi recarti a quello più vicino per consegnare il tuo libro\n'
        for totem in r:
            descrizione += 'Totem {}, {}, {}\n'.format(totem['totem_id'], totem['indirizzo'], totem['maps_link'])
        update.message.reply_text(descrizione, parse_mode='HTML')
    except Exception as e:
        print("ERRORE: {}".format(e))
        update.message.reply_text("Errore nella lettura dei totem liberi")

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
    dp.add_handler(CommandHandler("consegna", consegna))
    
    updater.start_polling()
    return updater

#MAIN
if __name__ == '__main__':
    updater = startBot()
    updater.idle()