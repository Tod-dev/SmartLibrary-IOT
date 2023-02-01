const db = require("../dbConn");

/*
  getTotemData
  params: [id]
  ritorna il totem (dati del totem:posizione...) e i libri contenuti in quel totem 
*/
exports.getTotemData = async (req, res) => {
  try {

    const id = req.params.id;
    console.log("getTotemData - id totem received :", id);

    /*const { rows: totem } = await db.query(
      `
        select t.id as totem_id, t.indirizzo as indirizzo, s.id as num_scompartimento, l.nome as libro
        from libri l join scompartimenti s on (l.scompartimento_id = s.id)
        join totems t on (s.totem_id = t.id)
        where t.id = $1
        `,
      [id]
    );
    const { rows: libri } = await db.query(
      `
        select libri.*
        from libri
        join scompartimenti on (libri.scompartimento_id = scompartimenti.id)
        join totems on (totems.id = scompartimenti.totem_id)
        where totems.id = $1
        `,
      [id]
    );

    const res = {
      totem: totem,
      libri: libri
    };*/
    const { rows: totem } = await db.query(
      `
        select t.*, s.id as scompartimento_id, s.stato as stato_scompartimento, l.nome as nome_libro
        from scompartimenti s join totems t on (s.totem_id = t.id) left join libri l on (l.scompartimento_id = s.id)
        where t.id = $1
        order by scompartimento_id asc
        `,
      [id]
    );
    

    return totem;
  } catch (error) {
    throw error;
  }
};

/*
  getTotemsFree 
  params: [query]
  ritorna i totem con almeno uno scompartimento libero
*/
exports.getTotemsFree = async (req, res) => {
  try {

    console.log("getTotemsFree - query received");

    const { rows } = await db.query(
      `select distinct t.id as totem_id, t.indirizzo as indirizzo, t.maps_link
       from scompartimenti s join totems t on (s.totem_id = t.id)
       where s.stato = 'libero'`,
      []
    );
    return rows;
  } catch (error) {
    throw error;
  }
};

/*
  getTotemsFromBook 
  params: [nomeLibro]
  ritorna i totem che contengono quel libro 
*/
exports.getTotemsFromBook = async (req, res) => {
  try {

    const bookname = req.query.nomeLibro ? req.query.nomeLibro : "";
    console.log("getTotemsFromBook - bookname received :", bookname);

    const { rows } = await db.query(
      `select distinct t.id as totem_id, l.scompartimento_id, l.id as libro_id
       from libri l join scompartimenti s on (l.scompartimento_id = s.id) 
       join totems t on (t.id = s.totem_id)
       where LOWER(l.nome) like LOWER(concat('%','${bookname}','%')) and 
          l.scompartimento_id is not null and 
          s.stato = 'occupato'`,
      []
    );
    return rows;
  } catch (error) {
    throw error;
  }
};