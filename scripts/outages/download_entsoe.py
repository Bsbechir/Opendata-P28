from entsoe import EntsoePandasClient
import pandas as pd

client = EntsoePandasClient(api_key='229ab3e0-7f5d-41b3-9fdc-8ed9a1f73a48')

start = pd.Timestamp('20150101', tz='Europe/Paris')
end = pd.Timestamp('20260101', tz='Europe/Paris')

print("Telechargement des indisponibilites FR...")
df = client.query_unavailability_of_generation_units('FR', start=start, end=end)

print(f"{len(df)} lignes telechargees")
print(df.columns.tolist())

df.to_csv('output/indisponibilites_entsoe.csv', sep=';')
print("Sauvegarde dans output/indisponibilites_entsoe.csv")
