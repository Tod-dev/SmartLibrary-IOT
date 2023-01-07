const router = require("express").Router();
const libri_controller = require("../controllers/libri_controller");

router.get("/", (req, res, next) => {
  libri_controller
    .getLibri(req, res)
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