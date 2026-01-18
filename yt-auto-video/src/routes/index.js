const express = require("express");
const router = express.Router();

const imageRoutes = require("./image.routes");
const projectRoutes = require("./project.routes");

// API Routes
router.use("/", imageRoutes);
router.use("/projects", projectRoutes);

module.exports = router;
