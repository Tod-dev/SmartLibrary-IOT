const db = require("../dbConn");


exports.getLibri = async (req, res) => {
    try {
    //   console.log("params:", req.query);
    //   const dataDa = req.query.da ? req.query.da : "19000101";
    //   const dataA = req.query.a ? req.query.a : "30000101";
  
      const { rows } = await db.query(
        `select * from libro`,
        []
      );

      return rows;
    } catch (error) {
      //pass error to next()
      throw error;
    }
  };