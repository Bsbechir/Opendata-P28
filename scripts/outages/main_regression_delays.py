#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Compare la durée annoncée initialement d'un arrêt avec la durée réellement observée.
# Utile pour quantifier le biais de révision systématique sur une unité donnée.

from pub_data_visualization import global_var, outages

data_source_outages = global_var.data_source_outages_rte
map_code            = global_var.geography_map_code_france
producer_outages    = None
production_source   = global_var.production_source_nuclear
unit_name           = 'CHINON 2'
date_min            = None
date_max            = None

figsize    = global_var.figsize_horizontal_ppt
folder_out = global_var.path_plots
close      = False

df = outages.load(
    source             = data_source_outages,
    map_code           = map_code,
    producer           = producer_outages,
    unit_name          = unit_name,
    production_source  = production_source,
    publication_dt_min = date_min,
    publication_dt_max = date_max,
)

outages.plot.regression_delays(
    df,
    source            = data_source_outages,
    producer          = producer_outages,
    production_source = production_source,
    unit_name         = unit_name,
    figsize           = figsize,
    close             = close,
    folder_out        = folder_out,
)
