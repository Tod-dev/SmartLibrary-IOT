//! Importing packages
const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");

//!import routes
const routes_totems = require("./routes/totems");
const routes_prenotazioni = require("./routes/prenotazioni");
const { unknownEndpoint } = require("./routes/default");

//!configuration
const app = express();
dotenv.config();
app.use(cors());
app.use(express.json());




//!Route Middlewares
app.use("/totems", routes_totems);
app.use("/prenotazioni", routes_prenotazioni);
app.use(unknownEndpoint);

//!Server listening
app.listen(process.env.PORT,() => start());

const start = () => {
  console.log(`App running on port ${process.env.PORT}.`);
};
