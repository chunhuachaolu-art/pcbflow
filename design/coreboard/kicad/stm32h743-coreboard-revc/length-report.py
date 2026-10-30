#!/usr/bin/env python
"""Rev-C length report (routing-spec §3): per-group length matching.

Usage (F:/kicad/bin/python.exe):  length-report.py
Prints JSON to stdout: per group, per-net copper length (pad-to-pad track
sum + 0.2mm per via), reference net, delta, target/limit, pass flags.
Read-only (board + report input; no filesystem writes).
"""
import json, os, re
import pcbnew

BOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stm32h743-coreboard-revc.kicad_pcb')
MM = 1000000
VIA_EQUIV = 0.2  # mm per via, spec §3 measurement convention

GROUPS = {
    'G_USB': {'ref': None, 'target': 1.0, 'limit': 2.5,
              'nets': ['USB_DP', 'USB_DM']},
    'G_FMC_D': {'ref': 'FMC_SDCLK', 'target': 2.5, 'limit': 5.0,
                'nets': [f'FMC_D{i}' for i in range(16)] + ['FMC_NBL0', 'FMC_NBL1']},
    'G_FMC_C': {'ref': 'FMC_SDCLK', 'target': 2.5, 'limit': 5.0,
                'nets': ['FMC_SDNCAS', 'FMC_SDNRAS', 'FMC_SDNWE', 'FMC_SDNE0', 'FMC_SDCKE0']},
    'G_FMC_A': {'ref': 'FMC_SDCLK', 'target': 5.0, 'limit': 10.0,
                'nets': [f'FMC_A{i}' for i in range(13)] + ['FMC_BA0', 'FMC_BA1']},
    'G_EMMC': {'ref': 'SDMMC2_CK', 'target': 1.5, 'limit': 3.0,
               'nets': ['SDMMC2_CMD'] + [f'SDMMC2_D{i}' for i in range(4)]},
    'G_SD': {'ref': 'SDMMC1_CK', 'target': 2.5, 'limit': 5.0,
             'nets': ['SDMMC1_CMD'] + [f'SDMMC1_D{i}' for i in range(4)] + ['SD_CD']},
    'G_QSPI': {'ref': 'QSPI_CLK', 'target': 2.5, 'limit': 5.0,
               'nets': [f'QSPI_IO{i}' for i in range(4)] + ['QSPI_NCS']},
    'G_ETH': {'ref': 'ETH_REF_CLK', 'target': 2.5, 'limit': 5.0,
              'nets': ['ETH_CRS_DV', 'ETH_RXD0', 'ETH_RXD1', 'ETH_TXD0', 'ETH_TXD1',
                       'ETH_TX_EN', 'ETH_MDC', 'ETH_MDIO']},
    'G_LTDC': {'ref': 'LTDC_PCLK', 'target': 5.0, 'limit': 10.0,
               'nets': [f'LTDC_R{i}' for i in range(5)] + [f'LTDC_G{i}' for i in range(6)] +
                       [f'LTDC_B{i}' for i in range(5)] + ['LTDC_DE', 'LTDC_HSYNC', 'LTDC_VSYNC']},
}

def main():
    b = pcbnew.LoadBoard(BOARD)
    by_net = {}
    for t in b.GetTracks():
        nc = t.GetNetCode()
        if nc not in by_net:
            by_net[nc] = [0.0, 0]  # length, vias
        if t.GetClass() == 'PCB_TRACK':
            by_net[nc][0] += t.GetLength() / MM
        elif t.GetClass() == 'PCB_VIA':
            by_net[nc][1] += 1
    name2len = {}
    for code, (length, vias) in by_net.items():
        net = b.GetNetInfo().GetNetItem(code)
        if net:
            name2len[net.GetNetname()] = length + vias * VIA_EQUIV

    report = {'groups': {}, 'all_pass': True}
    for gname, g in GROUPS.items():
        entry = {'target_mm': g['target'], 'limit_mm': g['limit'], 'nets': {}}
        if g['ref'] is None:
            # USB intra-pair
            lens = {n: round(name2len.get(n, 0.0), 2) for n in g['nets']}
            entry['nets'] = lens
            if all(v > 0 for v in lens.values()):
                delta = round(abs(lens[g['nets'][0]] - lens[g['nets'][1]]), 2)
                entry['intra_pair_delta_mm'] = delta
                entry['pass'] = delta <= g['limit']
            else:
                entry['pass'] = False
                entry['note'] = 'unrouted'
        else:
            ref_len = name2len.get(g['ref'])
            worst = 0.0
            for n in g['nets'] + [g['ref']]:
                entry['nets'][n] = round(name2len.get(n, 0.0), 2)
            if ref_len is None or ref_len <= 0:
                entry['pass'] = False
                entry['note'] = 'reference unrouted'
            else:
                deltas = {}
                for n in g['nets']:
                    d = name2len.get(n, 0.0) - ref_len
                    deltas[n] = round(d, 2)
                    worst = max(worst, abs(d))
                entry['deltas_vs_ref'] = deltas
                entry['ref_len_mm'] = round(ref_len, 2)
                entry['worst_abs_delta_mm'] = round(worst, 2)
                entry['pass'] = worst <= g['limit']
                entry['target_met'] = worst <= g['target']
        if not entry.get('pass'):
            report['all_pass'] = False
        report['groups'][gname] = entry
    print(json.dumps(report, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
