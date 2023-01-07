//! Importing packages
const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");

//!import routes
const routes_libri = require("./routes/libri");
const { unknownEndpoint } = require("./routes/default");

//!configuration
const app = express();
dotenv.config();
app.use(cors());
app.use(express.json());

//!PostgreSQL connection & TEST

//!Route Middlewares
app.use("/libri", routes_libri);
app.use(unknownEndpoint);

//!Server listening
app.listen(
    5000//process.env.PORT,
     ,() => start());

const start = () => {
  console.log(`App running on port ${process.env.PORT}.`);
};