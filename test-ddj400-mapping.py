import importlib.util
import pathlib
import tempfile

spec = importlib.util.spec_from_file_location(
    'ddj400_bridge', pathlib.Path(__file__).with_name('ddj400-rx3.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

controls = [
    ('[Channel1]', 'play', 0x90, 0x0B),
    ('[Channel1]', 'PioneerDDJ400.syncPressed', 0x90, 0x58),
    ('[Channel1]', 'PioneerDDJ400.syncLongPressed', 0x90, 0x5C),
    ('[Channel1]', 'PioneerDDJ400.toggleQuantize', 0x90, 0x68),
    ('[Library]', 'MoveVertical', 0xB6, 0x40),
    ('[Library]', 'MoveFocusForward', 0x96, 0x41),
    ('[Library]', 'MoveFocusBackward', 0x96, 0x42),
    ('[Channel1]', 'hotcue_1_activate', 0x97, 0x00),
    ('[Channel1]', 'PioneerDDJ400.beatjumpPadPressed', 0x97, 0x20),
    ('[Channel1]', 'beatloop_0.25_toggle', 0x97, 0x60),
]
xml = '<root><controls>' + ''.join(
    f'<control><group>{group}</group><key>{key}</key><status>{status}</status>'
    f'<midino>{note}</midino></control>'
    for group, key, status, note in controls) + '</controls></root>'

with tempfile.NamedTemporaryFile(mode='w', suffix='.xml') as mapping:
    mapping.write(xml)
    mapping.flush()
    events = []
    bridge = module.Bridge(mapping.name, lambda *event: events.append(event))
    assert len(bridge.mapping) == len(controls), bridge.mapping
    for packet in (
        [0x90, 0x0B, 127, 0x80, 0x0B, 0],
        [0x90, 0x58, 127, 0x80, 0x58, 0],
        [0x90, 0x5C, 127, 0x80, 0x5C, 0],
        [0x90, 0x68, 127, 0x80, 0x68, 0],
        [0xB6, 0x40, 1, 0x40, 127],
        [0x96, 0x41, 127],
        [0x96, 0x42, 127],
        [0x97, 0x00, 127, 0x87, 0x00, 0],
        [0x97, 0x20, 127, 0x87, 0x20, 0],
        [0x97, 0x60, 127, 0x87, 0x60, 0],
    ):
        bridge.feed(packet)

assert events[0][:3] == (0x4101, 0, 1), events
assert any(event[:3] == (0x4112, 0, 1) for event in events), events
assert any(event[:3] == (0x4111, 0, 1) for event in events), events
assert any(event[:3] == (0x410B, 0, 1) for event in events), events
assert any(event == (0x420C, 4, 0, 1, 0.0, 0x4252) for event in events), events
assert any(event[:3] == (0x4117, 0, 1) and event[5] == 0x5040 for event in events), events
assert any(event[:3] == (0x4117, 0, 1) and event[5] == 0x5043 for event in events), events
assert any(event[:3] == (0x4117, 0, 1) and event[5] == 0x5041 for event in events), events
print('PASS DDJ-400 transport, sync, quantize, browse and pad-bank mappings')
