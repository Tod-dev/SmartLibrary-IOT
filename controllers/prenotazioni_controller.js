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
    const codice = 1;
    MqttHandler.sendMessage(totem_id,`${scompartimento_id}/${codice}/${id_prenotazione}`)

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
    const id_prenotazione = req.params.id;
    const body = req.body;
    console.log(body);
    const stato = body["stato"];

    if (!stato) {
      throw { error: "stato is missing" };
    }

    if (stato != 'prenotato' && stato != 'prelevato' && stato != 'consegnato') {
      throw { error: "stato is wrong: value must be in (prenotato, prelevato, consegnato) " };
    }

    const {rows: dati_prenotazione} = await db.query(`
      select scompartimenti.id as scompartimento_id, totems.id as totem_id
      from prestiti
      join libri on (libri.id = prestiti.libro_id)
      join scompartimenti on (libri.scompartimento_id = scompartimenti.id)
      join totems on (scompartimenti.totem_id = totems.id)
      where prestiti.id = $1`,
      [id_prenotazione]
    )
    if (dati_prenotazione.length == 0){
      throw { error: "dati_prenotazione non esistenti" };
    }
    const scompartimento_id = dati_prenotazione[0]["scompartimento_id"];
    const totem_id = dati_prenotazione[0]["totem_id"];

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
    /* SEND MQTT MESSAGE */
    //IDSCOMPARTIMENTO/CODICE/ID_PRENOTAZIONE
    let codice;
    if (stato === 'consegnato'){
      codice = 3;
    }
    else if (stato === 'prelevato'){
      codice = 2;
    }
    else{
      throw { error: "STATO NON VALIDO" };
    }
    MqttHandler.sendMessage(totem_id,`${scompartimento_id}/${codice}/${id_prenotazione}`)
    return { json: `Prestito ${id_prenotazione} aggiornato allo stato ${stato} correttamente` };
  } catch (error) {
    throw error;
  }
};
