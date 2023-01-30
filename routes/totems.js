const router = require("express").Router();
const totems_controller = require("../controllers/totems_controller");

//GET localhost:5000/totems?nomeLibro=NOMELIBRO
//GET localhost:5000/totems?query=liberi 
router.get("/", (req, res, next) => {
  if(req.query.nomeLibro != null){
    totems_controller
      .getTotemsFromBook(req, res)
      .then((response) => {
        //console.log("RESPONSE:", response);
        res.status(200).json(response);
      })
      .catch((error) => {
        console.log("ERROR:", error);
        res.status(400).json(error);
      });
  }
  else if(req.query.query != null){
    totems_controller
      .getTotemsFree(req, res)
      .then((response) => {
        //console.log("RESPONSE:", response);
        res.status(200).json(response);
      })
      .catch((error) => {
        console.log("ERROR:", error);
        res.status(400).json(error);
      });
  }
});

//GET /totems/IDTOTEM  -> getTotemData
router.get("/:id", (req, res, next) => {
  totems_controller
    .getTotemData(req, res)
    .then((response) => {
      //console.log("RESPONSE:", response);
      res.status(200).json(response);
    })
    .catch((error) => {
      console.log("ERROR:", error);
      res.status(400).json(error);
    });
});

module.exports = router;