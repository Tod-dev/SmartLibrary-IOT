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
    return ['prenota','consegna','consigliami']

#COMANDI
def start(update, context):
    """Send a message when the command /now is issued."""
    username = update.message.chat.username
    update.message.reply_text('Hello, {}!\n/help for documentation.'.format(username))

def help(update, context):
    """Send a message when the command /now is issued."""
    operazioniDesc = map(lambda x: '/{} , {} un libro.'.format(x,x), getOperations())
    text = '\n'.join(operazioniDesc)
    text += '\n'+'/totem , visualizza i libri contenuti in un totem'
    update.message.reply_text(text)


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

def consigliami(update, context):
    """Send a message when the command /consigliami is issued."""
    print(update.message.text)
    #RITORNARE La lista di libri consigliati dall'ai
    msg = update.message.text.split('/consigliami ')
    username = update.message.chat.username

    r = requests.get('{}/prenotazioni/last/libro?utente={}'.format(SERVER_URL, username))
    if r.text == '[]':
        update.message.reply_text("Spiacenti, errore nel reperimento dell'ultimo libro letto")
        return
    
    r = json.loads(r.text)
    print(r)
    hasAtLeastOneReading = True
    if(r["id"] == -1):
        hasAtLeastOneReading = False
    

    if len(msg) == 1 and (not hasAtLeastOneReading):
        #ho solo la scritta /consigliami
        return update.message.reply_text("Per consigliarti un libro scrivi /consigliami seguito dal nome dell' ultimo libro che hai letto ")
    try:
        if hasAtLeastOneReading and r["libro"] and len(msg) == 1:
            libro = r["libro"] 
        else:
            libro = msg[1]
        print(libro)
        r = requests.get('https://data.readow.ai/api/titles/quick/0?tokens={}'.format(libro))
        print(r.text)
        if r.text == '[]':
            update.message.reply_text('Spiacenti, ma non trovo il libro che hai inserito')
            return        
        r = json.loads(r.text)[0]
        # "bookId": "30366603-prova-ad-amarmi-ancora",
        # "title": "Prova ad amarmi ancora",
        # "isbn": "B01CZ8920S",
        # "workId": "50878346-prova-ad-amarmi-ancora",
        # "language": "italian",
        # "author": "Sylvia Kant",
        # "search": null,
        # "popular": 0.000053165088,
        # "hasCover": false,
        # "coverLink": null
        print(r)
        r = requests.get('https://data.readow.ai/api/transformer?id={}'.format(r["workId"]))
        print(r.text)
        if r.text == '[]':
            update.message.reply_text('Spiacenti, ma non trovo il libro che hai inserito')
            return        
        r = json.loads(r.text)        
        update.message.reply_text("Ecco alcuni libri che ti consiglio", parse_mode='HTML')
        count = 0
        for l in r:
            count += 1
            update.message.reply_text(l["title"] + '-' + ' Author: '+ l["author"], parse_mode='HTML')
            img = l["coverLink"]
            if img != "":
                url = img
                response = requests.get(url)    
                update.message.reply_photo(photo=BytesIO(response.content))
            if count == 3:
                break

    except Exception as e:
        print("ERRORE: {}".format(e))
        update.message.reply_text("Errore nella lettura dei totem liberi")

def totem(update, context):
    """Send a message when the command /now is issued."""
    print(update.message.text)
    
    msg = update.message.text.split('/totem ')
    if len(msg) == 1:
        #ho solo la scritta /prenota
        return update.message.reply_text("Per vedere i libri contenuti in un totem inserisci /totem seguito dal numero del totem")
        
    try:

        #ho anche l'id del totem
        id = msg[1]
        
        r = requests.get('{}/totems/{}'.format(SERVER_URL, id))
        print(r.text)
        if r.text == '[]':
            update.message.reply_text('Il totem {} non è attivo'.format(id))
            return
        
        r = json.loads(r.text)
        risposta = 'Ecco i libri contenuti nel totem {}\n'.format(id)
        num_libri = 0
        for libro in r:
            nome_libro = libro['nome_libro']
            disponibilita = libro['stato_scompartimento']

            if disponibilita == 'occupato':
                disponibilita = 'disponibile'

            if nome_libro is not None:
                risposta += '{}, <b>{}</b>\n'.format(nome_libro, disponibilita)
                num_libri += 1

        if num_libri == 0:
            update.message.reply_text('Il totem {} è vuoto al momento'.format(id))
        else:
            update.message.reply_text(risposta, parse_mode='HTML')
    except Exception as e:
        print("ERRORE: {}".format(e))
        update.message.reply_text("Errore nella lettura dei libri del totem")

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
    dp.add_handler(CommandHandler("consigliami", consigliami))
    dp.add_handler(CommandHandler("totem", totem))
    
    updater.start_polling()
    return updater

#MAIN
if __name__ == '__main__':
    updater = startBot()
    updater.idle()