const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function userRoutes(controller, adminOnly) {
    const router = express.Router();

    router.delete('/users/:id', adminOnly, asyncHandler(async (req, res) => {
        res.send(await controller.remove(req.params.id));
    }));

    return router;
}

module.exports = userRoutes;
