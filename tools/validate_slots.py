"""Semantic validation for optional versioned asset compatibility and named presets."""
from __future__ import annotations


def check(packs):
    """Packs are schema-validated, uniquely named pack dictionaries. Return descriptive errors."""
    errors, assets, interfaces = [], {}, {}
    for pack in packs:
        for contract_id, definition in pack.get('interfaces', {}).items():
            if not contract_id.endswith('/1'):
                errors.append(f'Interface ID must include /1 version: {contract_id}')
            if contract_id in interfaces and interfaces[contract_id] != definition:
                errors.append('Conflicting interface ' + contract_id)
            interfaces[contract_id] = definition
        for asset in pack.get('assets', []):
            if asset['id'] in assets: errors.append('Duplicate asset ' + asset['id'])
            assets[asset['id']] = asset

    def size(asset_id, visited=None):
        visited = visited or set()
        if asset_id in visited: raise ValueError('Size-reference cycle ' + asset_id)
        a = assets.get(asset_id)
        if not a: raise ValueError('Unknown asset ' + asset_id)
        visited.add(asset_id)
        if a['kind'] == 'region': return a.get('logical_size_px', a['rect_px'][2:4])
        if a['kind'] == 'composition': return a['size_px']
        if a['kind'] == 'sequence': return size(a['frames'][0]['asset'], visited)
        if a['kind'] == 'state_set': return size(a['states'][a['default_state']], visited)
        raise ValueError('Unknown kind ' + a['kind'])

    for asset in assets.values():
        for interface_id in asset.get('implements', []):
            c = interfaces.get(interface_id)
            if c is None: errors.append(asset['id'] + ' implements missing ' + interface_id); continue
            try:
                actual = size(asset['id'])
                if not c['allow_scale'] and actual != c['size_px']:
                    errors.append(asset['id'] + ' incompatible dimensions for ' + interface_id)
            except (KeyError, ValueError) as exc: errors.append(str(exc))
        if asset['kind'] != 'composition': continue
        slots = asset.get('slots', {})
        used = set()
        for layer in asset['layers']:
            if 'slot' in layer:
                used.add(layer['slot'])
                if layer['slot'] not in slots: errors.append(asset['id'] + ' undeclared layer slot ' + layer['slot'])
        for key, slot in slots.items():
            if key not in used: errors.append(asset['id'] + ' unused slot ' + key)
            contract = slot['accepts']
            if contract not in interfaces: errors.append(asset['id'] + ' unknown interface ' + contract)
            if slot['default'] not in slot['options']: errors.append(asset['id'] + ' default not in options ' + key)
            for choice in slot['options']:
                target = assets.get(choice)
                if not target: errors.append(asset['id'] + ' missing choice ' + choice)
                elif contract not in target.get('implements', []): errors.append(choice + ' lacks interface ' + contract)
        for name, preset in asset.get('presets', {}).items():
            for key, value in preset.get('slots', {}).items():
                if key not in slots or value not in slots[key]['options']:
                    errors.append(asset['id'] + ': bad preset slot ' + name + '/' + key)
            for key, value in preset.get('inputs', {}).items():
                spec = asset.get('inputs', {}).get(key)
                valid = (spec and ((spec['type'] == 'boolean' and type(value) is bool)
                            or (spec['type'] == 'number' and type(value) in (int, float) and spec.get('min', float('-inf')) <= value <= spec.get('max', float('inf')))
                            or (spec['type'] == 'enum' and value in spec['values'])))
                if not valid: errors.append(asset['id'] + ': bad preset input ' + name + '/' + key)
        if asset.get('default_preset') and asset['default_preset'] not in asset.get('presets', {}):
            errors.append(asset['id'] + ': unknown default preset')
    return errors
