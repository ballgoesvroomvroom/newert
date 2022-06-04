const express = require("express");

const app = express();

app.use(express.static("public"))

app.get("/", (req, res) => {
	res.type("html")
	res.sendFile("index.html")
});

app.listen(5000, () => console.log("5000"));