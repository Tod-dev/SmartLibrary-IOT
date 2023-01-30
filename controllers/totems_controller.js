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

    const { rows: totem } = await db.query(
      `
        select totems.*
        from totems
        where totems.id = $1
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
    };

    return res;
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
      /*`
      select distinct totems.id as totem_id, libri.scompartimento_id, libri.id as libro_id
      from libri
      join scompartimenti on (libri.scompartimento_id = scompartimenti.id)
      join totems on (totems.id = scompartimenti.totem_id)
      where libri.nome like concat('%','${bookname}','%')
      `,*/
      `select distinct t.id as totem_id, l.scompartimento_id, l.id as libro_id
       from libri l join scompartimenti s on (l.scompartimento_id = s.id)
       join totems t on (s.totem_id = t.id)
       where l.nome like concat('%','${bookname}','%') and l.id not in(
       select distinct p.libro_id
       from prestiti p 
       where p.data_fine_prestito is null)`,
      []
    );
    return rows;
  } catch (error) {
    throw error;
  }
};