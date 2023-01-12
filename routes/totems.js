const router = require("express").Router();
const totems_controller = require("../controllers/totems_controller");

//GET localhost:5000/totems?nomeLibro=NOMELIBRO 
router.get("/", (req, res, next) => {
  totems_controller
    .getTotemsFromBook(req, res)
    .then((response) => {
      //console.log("RESPONSE:", response);
      res.status(200).json(response);
    })
    .catch((error) => {
      console.log("ERROR:", error);
      res.status(500).json(error);
    });
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
      res.status(500).json(error);
    });
});

module.exports = router;