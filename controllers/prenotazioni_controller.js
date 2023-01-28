const db = require("../dbConn");
const MqttHandler = require("../MqttHandler");


/*
  insertPrenotazione
  params  [utente_id,libro_id,scompartimento_id]
  body: {
    "libro_id": 1,
    "utente": "matteberto99",
    "scompartimento_id": 3,
    "totem_id": 2
  }
  Inserisce una nuova prenotazione di un libro su un totem (parametri nel body)
*/
exports.insertPrenotazione = async (req, res) => {
  try {
    const body = req.body;
    console.log(body);
    libro = body["libro_id"];
    utente = body["utente"];
    scompartimento_id = body["scompartimento_id"];
    totem_id = body["totem_id"];

    if (!libro || !utente || !scompartimento_id || !totem_id) {
      throw { error: "libro or utente or scompartimento_id or totem_id is missing" };
    }

    const {rows: utente_rows} = await db.query(`
      select  utenti.id 
      from utenti 
      where utenti.username = $1`,
      [utente]
    )
    if (utente_rows.length == 0){
      throw { error: "username non esistente" };
    }
    const utente_id = utente_rows[0]["id"];

    const {rows: dati_totem} = await db.query(`
    select  totems.maps_link, totems.indirizzo 
    from totems 
    where totems.id = $1`,
    [totem_id]
  )
  if (dati_totem.length == 0){
    throw { error: "dati_totem non presenti" };
  }
  const maps_link = dati_totem[0]["maps_link"];
  const indirizzo = dati_totem[0]["indirizzo"];

    const {rows} = await db.query(`select nextval('serialPrestiti')`)
    const id_prenotazione = rows[0]["nextval"];
    await db.query(
      `insert into prestiti (id,utente_id,libro_id,data_inizio_prestito,data_fine_prestito,stato) 
      VALUES ($1, $2, $3, now(),NULL, 'prenotato')`,
      [
        id_prenotazione,
        utente_id,
        libro
      ]
    );
    /* SEND MQTT MESSAGE */
    //IDSCOMPARTIMENTO/CODICE/ID_PRENOTAZIONE
    MqttHandler.sendMessage(totem_id,`${scompartimento_id}/1/${id_prenotazione}`)

    return { id: id_prenotazione, descrizione: `Prestito inserito correttamente, PRENOTAZIONE NUMERO: <b>${id_prenotazione}</b>\n${indirizzo}\n${maps_link}` };
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
