# ipc map: IPC subclasses created after IPC 2006 (not in ALP) -> ALP subclasses
#
# inputs  (data/raw/external):
#   ipc4_to_isic_rev4_3_excl_service.txt        ALP, built on IPC 2006
#   20270101_inventory_of_IPC_ever_used_symbols.csv  WIPO: every IPC symbol ever used
#   ipc_rcl/ipc_concordancelist_YYYY0101.zip    WIPO revision concordance lists, 2018-2027
# output  (data/interim):
#   ipc_new_to_old.csv   new4, old4, n_groups, share, versions
#
# method: an RCL lists, for each IPC version, where groups were transferred (from-symbol -> to-symbol).
# for each subclass not in ALP, count the groups transferred into it from each other subclass,
# across all versions; share = groups from that predecessor / all groups transferred in.
# if a predecessor is itself not in ALP (e.g. H10D -> H10P), its own shares are chained until ALP is reached.

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

# paths
root     = Path(__file__).resolve().parent.parent
ext      = root / 'data' / 'raw' / 'external'
in_alp   = ext / 'ipc4_to_isic_rev4_3_excl_service.txt'
in_inv   = ext / '20270101_inventory_of_IPC_ever_used_symbols.csv'
in_rcl   = sorted((ext / 'ipc_rcl').glob('ipc_concordancelist_*.zip'))
out_map  = root / 'data' / 'interim' / 'ipc_new_to_old.csv'

ns = {'m': 'http://www.wipo.int/classifications/ipc/masterfiles'}

# 1. subclasses to map: created after 2006-01-01 and not in ALP (drops pre-2006 expired and X99Z residual codes)
alp = set(pd.read_csv(in_alp, dtype=str)['ipc4'])
inv = pd.read_csv(in_inv, sep=';', header=None, names=['sym', 'created', 'expired'], dtype=str)
sub = inv[inv['sym'].str.len() == 4]
new = sorted(sub.loc[(sub['created'] > '20060101') & ~sub['sym'].isin(alp), 'sym'])
print(f'subclasses to map: {len(new)} -> {new}')

# 2. all group transfers across subclasses, every version
rows = []
for z in in_rcl:
    with zipfile.ZipFile(z) as f:
        xml = f.read(f.namelist()[0])
    r = ET.fromstring(xml)
    ver = r.get('to-version')
    for c in r.findall('m:concordance', ns):
        for t in c.findall('m:concordance-to', ns):
            rows.append((ver, c.get('from-symbol')[:4], t.get('to-symbol')))
rcl = pd.DataFrame(rows, columns=['version', 'old4', 'to_symbol']).drop_duplicates()
rcl['new4'] = rcl['to_symbol'].str[:4]
rcl = rcl[(rcl['old4'] != rcl['new4']) & rcl['new4'].isin(new)]
print(f'RCL files: {len(in_rcl)} ({in_rcl[0].stem[-8:]}-{in_rcl[-1].stem[-8:]}) | transfers into new subclasses: {len(rcl):,}')

# 3. direct shares: groups transferred into each new subclass, by predecessor
direct = (rcl.groupby(['new4', 'old4'])
             .agg(n_groups=('to_symbol', 'nunique'), versions=('version', lambda v: ','.join(sorted({x[:4] for x in v}))))
             .reset_index())
direct['share'] = direct['n_groups'] / direct.groupby('new4')['n_groups'].transform('sum')

# 4. chain predecessors that are themselves new, until every predecessor is in ALP
m = direct.copy()
for _ in range(10):
    todo = m['old4'].isin(new)
    if not todo.any():
        break
    step = m[todo].merge(direct[['new4', 'old4', 'share']].rename(columns={'new4': 'old4', 'old4': 'old4_next', 'share': 'share_next'}), on='old4')
    step = step.assign(old4=step['old4_next'], share=step['share'] * step['share_next']).drop(columns=['old4_next', 'share_next'])
    m = pd.concat([m[~todo], step])
m = (m.groupby(['new4', 'old4'], as_index=False)
      .agg(n_groups=('n_groups', 'sum'), share=('share', 'sum'), versions=('versions', lambda v: ','.join(sorted(set(','.join(v).split(',')))))))

# 5. checks and save
assert m['old4'].isin(alp).all(), f'predecessors not in ALP: {sorted(set(m["old4"]) - alp)}'
assert (m.groupby('new4')['share'].sum().round(6) == 1).all()
missing = sorted(set(new) - set(m['new4']))
print(f'no predecessor found: {missing}')

m = m.sort_values(['new4', 'share'], ascending=[True, False])
m.to_csv(out_map, index=False)
print(m.round(3).to_string(index=False))
print(f'saved: {out_map.name} ({len(m)} rows, {m["new4"].nunique()} subclasses)')
