const db = require("../dbConn");
const MqttHandler = require("../MqttHandler");


/*
  insertPrenotazione
  params  [utente_id,libro_id]
  body: {
    "libro": 1,
    "utente": 2
  }
  Inserisce una nuova prenotazione di un libro su un totem (parametri nel body)
*/
exports.insertPrenotazione = async (req, res) => {
  try {
    const body = req.body;
    console.log(body);
    libro = body["libro"];
    utente = body["utente"];

    if (!libro || !utente) {
      throw { error: "libro or utente is missing" };
    }

    const {rows} = await db.query(`select nextval('serialPrestiti')`)
    const id = rows[0]["nextval"];
    console.log(id)
    await db.query(
      `insert into prestiti (id,utente_id,libro_id,data_inizio_prestito,data_fine_prestito,stato) 
      VALUES ($3, $1, $2, now(),NULL, 'prenotato')`,
      [
        utente,
        libro,
        id
      ]
    );
    /* SEND MQTT MESSAGE */
    //MQTT
    MqttHandler.sendMessage("CIAO2")

    return { id: id, descrizione: `Prestito inserito correttamente ${id}, Message sent to mqtt` };
  } catch (error) {
    throw error;
  }
};


/*
  updatePrenotazione
  params  [stato]
  body: {
    "stato": "prelevato"
  }
  Aggiorna lo stato della prenotazione (parametro stato: prenotato, prelevato, consegnato) 
*/
exports.updatePrenotazione = async (req, res) => {
  try {
    const id = req.params.id;
    const body = req.body;
    console.log(body);
    const stato = body["stato"];

    if (!stato) {
      throw { error: "stato is missing" };
    }

    if (stato != 'prenotato' && stato != 'prelevato' && stato != 'consegnato') {
      throw { error: "stato is wrong: value must be in (prenotato, prelevato, consegnato) " };
    }

    await db.query(
    `update prestiti 
    set stato = $2, 
    data_fine_prestito = ${stato === 'consegnato' ? 'now()' : 'NULL'}
    where id = $1 `,
      [
        id,
        stato
      ]
    );
    return { json: `Prestito ${id} aggiornato allo stato ${stato} correttamente` };
  } catch (error) {
    throw error;
  }
};
