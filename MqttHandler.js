const mqtt = require('mqtt');
const db = require("./dbConn");

let mqttConnection;
class MqttHandler {
  constructor() {
    this.mqttClient = null;
    this.options = {
      host: process.env.MQTT_BROKER,
      port: 8883,
      protocol: 'mqtts',
      username: process.env.MQTT_USERNAME,
      password: process.env.MQTT_PASSWORD
    }
    this.topicListening = 'TOTEMS/PRENOTAZIONI';
  }

  connect() {
    // Connect mqtt with credentials (in case of needed, otherwise we can omit 2nd param)
    this.mqttClient = mqtt.connect(this.options);

    // Mqtt error calback
    this.mqttClient.on('error', (err) => {
      console.log(err);
      this.mqttClient.end();
    });

    // Connection callback
    this.mqttClient.on('connect', () => {
      console.log(`mqtt client connected`);
    });

    // mqtt subscriptions
    this.mqttClient.subscribe(this.topicListening, { qos: 0 });

    // When a message arrives, console.log it
    this.mqttClient.on('message', async function (topic, message) {
      console.log(`MESSAGGIO MQTT RICEVUTO:\n  topic: ${topic}\n  message: ${message}`);
      message = message.toString();
      const npar = message.split('/').length;
      if (![3, 4].includes(npar)) {
        console.log("messaggio non definito!")
        return;
      }
      const parametri = message.split('/');
      if (parametri.includes(null) || parametri.includes(undefined) || parametri.includes('')) {
        console.log("Alcuni parametri non sono definiti!")
        return;
      }
      console.log("PARAMETRI RICEVUTI:", parametri);
      const [idtotem, id_prenotazione, stato, idscompartimento] = parametri;
      try {
        if (npar == 3) {
          await updatePrenotazioneStart(idtotem, id_prenotazione, stato);
        } else {
          //npar = 4
          if (!idscompartimento) {
            console.log("idscompartimento non definito")
            return;
          }
          await updatePrenotazioneEnd(idtotem, id_prenotazione, stato, idscompartimento);
        }
      } catch (e) {
        if (e.error) {
          //errore parametri utente
          console.log(e)
          mqttConnection.sendMessage(idtotem, e.error);
          return;
        }
        //errore server
        throw e;
      }

    });

    this.mqttClient.on('close', () => {
      console.log(`mqtt client disconnected`);
    });
  }

  // Sends a mqtt message to topic: mytopic
  sendMessage(topic, message) {
    this.mqttClient.publish('TOTEMS/' + topic, message);
  }
}

module.exports.connectMqtt = async () => {
  mqttConnection = new MqttHandler();
  mqttConnection.connect();
}

module.exports.getMqttConnection = () => {
  return mqttConnection;
}


module.exports.sendMessage = async (topic, message) => {
  mqttConnection.sendMessage(topic, message);
}

const updatePrenotazioneStart = async (idtotem, id_prenotazione, stato) => {
  try {
    if (stato != 'ritiro' && stato != 'consegna') {
      throw { error: "-1/stato is wrong: value must be in (ritiro, consegna) " };
    }
    const { stato_prestito_attuale, scompartimento_id_attuale, libro_id_attuale, nfc_libro } = await get_dati_prenotazione(id_prenotazione);
    if (stato == 'ritiro' && stato_prestito_attuale != 'prenotato') {
      throw { error: "-1/Il libro non è nello stato prenotato! Impossibile prelevarlo." };
    }
    if (stato == 'consegna' && stato_prestito_attuale != 'ritirato') {
      throw { error: "-1/Il libro non è nello stato ritirato! Impossibile consegnarlo." };
    }
    //TUTTO OK -> SEND MQTT MESSAGE: IDSCOMPARTIMENTO/CODICE/ID_PRENOTAZIONE
    const codice = stato === 'ritiro' ? 2 : 3;
    let scompartimento_assegnato = scompartimento_id_attuale;
    if (stato == 'consegna') {
      const { rows: nuovo_scompartimento } = await db.query(`
      select s.id as scompartimento_id
      from scompartimenti s join totems t on (s.totem_id = t.id)
      where s.stato = 'libero' and t.id = $1
      limit 1`,
        [idtotem]
      )
      if (nuovo_scompartimento.length == 0) {
        throw { erorr: `-1/Spiacenti, ma il totem non ha scompartimenti liberi al momento` }
      }
      scompartimento_assegnato = nuovo_scompartimento[0]["scompartimento_id"];
    }
    mqttConnection.sendMessage(idtotem, `${nfc_libro}/${scompartimento_assegnato}/${codice}/${id_prenotazione}`);
  }
  catch (error) {
    throw error;
  }
}

const updatePrenotazioneEnd = async (idtotem, id_prenotazione, stato, id_scompartimento) => {
  try {
    if (stato != 'ritirato' && stato != 'consegnato') {
      throw { error: "-1/stato is wrong: value must be in (ritirato, consegnato) " };
    }
    const { stato_prestito_attuale, scompartimento_id_attuale, libro_id_attuale, nfc_libro } = await get_dati_prenotazione(id_prenotazione);
    if (stato == 'ritirato' && stato_prestito_attuale != 'prenotato') {
      throw { error: "-1/Il libro non è nello stato prenotato! Impossibile prelevarlo." };
    }
    if (stato == 'consegnato' && stato_prestito_attuale != 'ritirato') {
      throw { error: "-1/Il libro non è nello stato ritirato! Impossibile consegnarlo." };
    }
    //TUTTO OK 
    // 1: AGGIORNA STATO PRENOTAZIONE
    await db.query(
      `update prestiti 
      set stato = $2, 
      data_fine_prestito = ${stato === 'consegnato' ? 'now()' : 'NULL'}
      where id = $1 `,
      [
        id_prenotazione,
        stato
      ]
    );
    // 2: AGGIORNA STATO LIBRO E SCOMPARTIMENTO
    const scomp = stato === 'consegnato' ? id_scompartimento : null
    await db.query(
      `update libri 
          set scompartimento_id = $1
          where id = $2 `,
      [
        scomp,
        libro_id_attuale
      ]
    );


    await db.query(
      `update scompartimenti 
        set stato = '${stato === 'consegnato' ? 'occupato' : 'libero'}'
        where id = $1 `,
      [
        id_scompartimento
      ]
    );
    //TUTTO OK
  }
  catch (error) {
    throw error;
  }
}

const get_dati_prenotazione = async (id_prenotazione) => {
  try {
    const { rows: stato_prestito_rs } = await db.query(`
      select stato,libri.scompartimento_id as scompartimento_id, libri.id as libro_id, libri."nfc-id" as nfc_libro
      from prestiti
      join libri on (libri.id = prestiti.libro_id)
      where prestiti.id = $1`,
      [id_prenotazione]
    )
    if (stato_prestito_rs.length == 0) {
      throw { error: "-1/prestito non esistente" };
    }
    const stato_prestito_attuale = stato_prestito_rs[0]["stato"];
    const scompartimento_id_attuale = stato_prestito_rs[0]["scompartimento_id"];
    const libro_id_attuale = stato_prestito_rs[0]["libro_id"];
    const nfc_libro = stato_prestito_rs[0]["nfc_libro"];
    return { stato_prestito_attuale, scompartimento_id_attuale, libro_id_attuale, nfc_libro };
  } catch (err) {
    throw err;
  }

}

      // switch (message) {
      //   case 'idtotem/idprenotazione/ritiro':
      //     break;
      //   case 'idtotem/idprenotazione/ritirato/idscomp':
      //     break;
      //   case 'idtotem/idprenotazione/ritiro':
      //     break;
      //   case 'idtotem/idprenotazione/consegnato/scompartimento':
      //     break;
      //   default:
      //     console.log("MQTT message not recognized!!!");
      //     break;
      // }