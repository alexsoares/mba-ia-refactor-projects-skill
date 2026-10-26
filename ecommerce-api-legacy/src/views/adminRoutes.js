const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function adminRoutes(controller, adminOnly) {
    const router = express.Router();

    router.get('/admin/financial-report', adminOnly, asyncHandler(async (req, res) => {
        res.json(await controller.financialReport());
    }));

    return router;
}

module.exports = adminRoutes;
