const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function checkoutRoutes(controller) {
    const router = express.Router();

    router.post('/checkout', asyncHandler(async (req, res) => {
        res.status(200).json(await controller.checkout(req.body));
    }));

    return router;
}

module.exports = checkoutRoutes;
