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

    const { rows: utente_rows } = await db.query(`
      select  utenti.id 
      from utenti 
      where utenti.username = $1`,
      [utente]
    )
    if (utente_rows.length == 0) {
      throw { error: "username non esistente" };
    }
    const utente_id = utente_rows[0]["id"];

    const { rows: dati_totem } = await db.query(`
    select  totems.maps_link, totems.indirizzo 
    from totems 
    where totems.id = $1`,
      [totem_id]
    )
    if (dati_totem.length == 0) {
      throw { error: "dati_totem non presenti" };
    }
    const maps_link = dati_totem[0]["maps_link"];
    const indirizzo = dati_totem[0]["indirizzo"];

    const { rows } = await db.query(`select nextval('serialPrestiti')`)
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
    await db.query(
      `update scompartimenti
       set stato = 'prenotato' where id = $1`,
      [
        scompartimento_id
      ]
    );
    /* SEND MQTT MESSAGE */
    //IDSCOMPARTIMENTO/CODICE/ID_PRENOTAZIONE
    const codice = 1;
    MqttHandler.sendMessage(totem_id, `${scompartimento_id}/${codice}/${id_prenotazione}`)

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
  Aggiorna lo stato della prenotazione (parametro stato: prenotato, prelevato,in consegna, consegnato ) 
*/
exports.updatePrenotazione = async (req, res) => {
  try {
    const id_prenotazione = req.params.id;
    const body = req.body;
    console.log(body);
    const stato = body["stato"];
    const totem_id = body["totem_id"];
    scompartimento_id = body["scompartimento_id"];

    if (!stato || !totem_id) {
      throw { error: "stato or totem_id is missing" };
    }

    if (stato == 'consegnato' && !scompartimento_id) {
      throw { error: "scompartimento_id is missing" };
    }

    if (stato != 'prelevato' && stato != 'consegnato' && stato != 'in consegna') {
      throw { error: "stato is wrong: value must be in (prelevato, consegnato, in consegna) " };
    }

    const { rows: stato_prestito_rs } = await db.query(`
      select stato
      from prestiti
      where id = $1`,
      [id_prenotazione]
    )
    if (stato_prestito_rs.length == 0) {
      throw { error: "prestito non esistente" };
    }

    stato_prestito = stato_prestito_rs[0]["stato"];

    if (stato == 'prelevato') {
      if(stato_prestito != 'prenotato'){
        throw { error: "Il libro non è nello stato prenotato! Impossibile prelevarlo." };
      }
      const { rows: dati_prenotazione } = await db.query(`
        select libri.scompartimento_id as scompartimento_id, libri.id as libro_id
        from prestiti
        join libri on (libri.id = prestiti.libro_id)
        where prestiti.id = $1`,
        [id_prenotazione]
      )
      if (dati_prenotazione.length == 0) {
        throw { error: "dati_prenotazione non esistenti" };
      }

      scompartimento_id = dati_prenotazione[0]["scompartimento_id"];

      await db.query(
        `update libri 
        set scompartimento_id = NULL
        where scompartimento_id = $1 `,
        [
          scompartimento_id
        ]
      );

      await db.query(
        `update scompartimenti 
        set stato = 'libero'
        where id = $1 `,
        [
          scompartimento_id
        ]
      );
    }

    if (stato == 'in consegna') {
      if(stato_prestito != 'prelevato'){
        throw { error: "Il libro non è nello stato prelevato! Impossibile passarlo in consegna." };
      }
      const { rows: nuovo_scompartimento } = await db.query(`
        select s.id as scompartimento_id
        from scompartimenti s join totems t on (s.totem_id = t.id)
        where s.stato = 'libero' and t.id = $1
        limit 1`,
        [totem_id]
      )

      if (nuovo_scompartimento.length == 0) {
        return { json: `Spiacenti, ma il totem non ha scompartimenti liberi al momento` };
      }

      scompartimento_id = nuovo_scompartimento[0]["scompartimento_id"];
    }


    if (stato == 'consegnato') {
      if(stato_prestito != 'in consegna'){
        throw { error: "Il libro non è nello stato in consegna! Impossibile consegnarlo." };
      }
      const { rows: dati_prenotazione } = await db.query(`
        select libri.id as libro_id
        from prestiti
        join libri on (libri.id = prestiti.libro_id)
        where prestiti.id = $1`,
        [id_prenotazione]
      )
      if (dati_prenotazione.length == 0) {
        throw { error: "dati_prenotazione non esistenti" };
      }

      const libro_id = dati_prenotazione[0]["libro_id"];

      await db.query(
        `update libri 
        set scompartimento_id = $1
        where id = $2 `,
        [
          scompartimento_id,
          libro_id
        ]
      );

      await db.query(
        `update scompartimenti 
        set stato = 'occupato'
        where id = $1 `,
        [
          scompartimento_id
        ]
      );
    }

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
    if (stato === 'in consegna') {
      codice = 3;
    }
    else if (stato === 'prelevato') {
      codice = 2;
    }
    else if (stato == 'consegnato') {
      return { json: `Prestito ${id_prenotazione} aggiornato allo stato ${stato} correttamente` };
    }
    else {
      throw { error: "STATO NON VALIDO" };
    }
    MqttHandler.sendMessage(totem_id, `${scompartimento_id}/${codice}/${id_prenotazione}`);

    if (stato == 'in consegna') {
      return { json: `Prestito ${id_prenotazione} aggiornato allo stato ${stato} correttamente, numero scompartimento: ${scompartimento_id}` };
    }

    return { json: `Prestito ${id_prenotazione} aggiornato allo stato ${stato} correttamente` };
  } catch (error) {
    throw error;
  }
};
