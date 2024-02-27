MATRIX
======


Metadata to store in PineAPPL grid
----------------------------------
The following is a more or less complete list of the metadata that should be
stored in a PineAPPL grid file. The list is not exhaustive, and some of the
metadata might not be relevant for all grids. However, it is a good starting
point for what to store in a grid file.

The commands below can all be performed simultaneously, 
however we break them down here for the sake of readability.


- **Optimise and scale** (if needed) the pineappl grid, this can be done  using pineappl’s  CLI: an example would be
    
    ``pineappl write —optimize —scale 0.001 name_old_grid.pineappl.lz4 name_new_grid.pineappl.lz4```

    In this case we have generated a new pineappl grid called 
    name_new_grid.pineappl.lz4. This grid has been optimised so as not to contain 
    useless zeros and rescaled by a factor ``0.001`` eg to go from pb to fb.

- **Delete useless keys** 
    Again, this can be done using pineappl write

    ``pineappl write —delete_key “y_label_unit” —delete_key  “xlabel”  “x_label-tex” name_old_grid.pineappl.lz4 name_new_grid.pineappl.lz4``
     
     Here we have removed some unwanted keys. Note that the available keys can be listed with:
    ``pineappl read --keys abseta_lep_NLO.QCD.pineappl.lz4``

- **Set Key values** to useful names: 
    In the example below, for instance, we are setting the y unit to the wanted unit, 
    the y label to be a differential cross section and the lumi id type so as to be compatible with LHAPDF
    
    ``pineappl write —set-key-value ‘y-unit’ ‘pb/GeV’  —set-key-value ‘y-label’ ‘differential x-sec’ —set-key-value ‘lumi_id_types’ ‘pdg_mc_ids’ name_old_grid.pineappl.lz4 name_new_grid.pineappl.lz4``

    Another key that should be added is the arXiv number.

- **Add output log of MATRIX**, 
    
    it was decided that the MATRIX output log should be added to pineappl grids for the sake of readability. To do so just run: 
    
    ``pineappl write —set-key-value ‘output_log’ ‘<the output log>’ name_old_grid.pineappl.lz4 name_new_grid.pineappl.lz4``

