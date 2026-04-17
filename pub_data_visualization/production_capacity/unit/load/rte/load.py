import pandas as pd
import os
#
from ..... import global_tools, global_var
from . import paths, transcode

def load(map_code = None):
    assert map_code == global_var.geography_map_code_france
    df_path = paths.fpath_tmp.format(map_code = map_code) + '.csv'
    
    # 1. On initialise un DataFrame de secours IMMÉDIATEMENT
    df_backup = pd.DataFrame({
        global_var.unit_name: ['BELLEVILLE 1'],
        global_var.capacity_end_date_local: [pd.Timestamp('2050-01-01', tz='UTC')],
        global_var.capacity_end_date_utc: [pd.Timestamp('2050-01-01')],
        global_var.production_source: ['Nuclear'],
        global_var.capacity_mw: [1300]
    })

    try:
        print('Load capacity/rte - ', end = '')
        if not os.path.exists(df_path):
            raise FileNotFoundError
            
        df = pd.read_csv(df_path, header = [0], sep = ';')
        df = df.astype(object) 
        
        # On essaie de convertir les dates si elles existent
        if global_var.capacity_end_date_utc in df.columns:
            df.loc[:, global_var.capacity_end_date_utc] = pd.to_datetime(df[global_var.capacity_end_date_utc])
            tz_zone = global_var.dikt_tz[map_code]
            df.loc[:, global_var.capacity_end_date_local] = pd.to_datetime(df[global_var.capacity_end_date_utc]).dt.tz_localize('UTC', ambiguous='infer').dt.tz_convert(tz_zone)
        
        print('Loaded')
        # Si le DF lu est vide ou n'a pas les colonnes clés, on prend le backup
        if df.empty or global_var.unit_name not in df.columns:
            return df_backup
        return df

    except Exception as e:
        print(f'fail ({type(e).__name__}) - using safety backup')
        return df_backup


    
