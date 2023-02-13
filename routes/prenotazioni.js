const router = require("express").Router();
const prenotazioni_controller = require("../controllers/prenotazioni_controller");

// POST localhost:5000/prenotazioni 
router.post("/", (req, res, next) => {
  prenotazioni_controller.insertPrenotazione(req, res)
    .then((response) => {
      //console.log("RESPONSE:", response);
      res.status(201).json(response);
    })
    .catch((error) => {
      console.log("ERROR:", error);
      res.status(400).json(error);
    });
});

//PUT localhost:5000/prenotazioni/IDPRENOTAZIONE
// router.put("/:id", (req, res, next) => {
//   prenotazioni_controller.updatePrenotazione(req, res)
//     .then((response) => {
//       //console.log("RESPONSE:", response);
//       res.status(201).json(response);
//     })
//     .catch((error) => {
//       console.log("ERROR:", error);
//       res.status(400).json(error);
//     });
// });



// POST localhost:5000/prenotazioni /last/libro 

router.get("/last/libro", (req, res, next) => {
  prenotazioni_controller.getLastLibroLetto(req, res)
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