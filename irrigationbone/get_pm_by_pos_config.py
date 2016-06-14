# -*- coding: utf-8 -*-
PM_COMPENSATION_COEF = { u'בית דגן' : 0.6, u'חוות מתתיהו': 0.6 , u'עכו': 0.6}
for k, v in PM_COMPENSATION_COEF.items():
    PM_COMPENSATION_COEF[k] = v/0.45
