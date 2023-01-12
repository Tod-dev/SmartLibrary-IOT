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
      `
      select distinct totems.*,libri.*
      from libri
      join scompartimenti on (libri.scompartimento_id = scompartimenti.id)
      join totems on (totems.id = scompartimenti.totem_id)
      where libri.nome like concat('%','${bookname}','%')
      `,
      []
    );
    return rows;
  } catch (error) {
    throw error;
  }
};