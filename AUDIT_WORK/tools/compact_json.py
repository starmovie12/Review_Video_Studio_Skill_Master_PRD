import json
def dumps(o, indent=0, width=150):
    one = json.dumps(o, ensure_ascii=False)
    if len(one) + indent <= width or not isinstance(o, (dict, list)) or not o:
        return one
    pad = ' ' * (indent + 2)
    if isinstance(o, dict):
        items = [f'{pad}{json.dumps(k, ensure_ascii=False)}: {dumps(v, indent + 2, width)}' for k, v in o.items()]
        return '{\n' + ',\n'.join(items) + '\n' + ' ' * indent + '}'
    items = [pad + dumps(v, indent + 2, width) for v in o]
    return '[\n' + ',\n'.join(items) + '\n' + ' ' * indent + ']'
