"""Fetch the pinned official Mixxx DDJ-400 mapping, or validate a user-supplied XML.

Orange Pi 4 LTS port: was BiteDJ's FLX6 mapping + flx6-rx3.py. See
DDJ400-PORT-NOTES.md for how this mapping was diffed against FLX6."""
import hashlib
import importlib.util
import urllib.request
from . import REPO
from .safefs import Tree
from .ui import Failure, ok, say

URL = ('https://raw.githubusercontent.com/mixxxdj/mixxx/'
       '6ff4e36eec76a0b3d66316dd8bad6155833b6ae6/res/controllers/Pioneer-DDJ-400.midi.xml')
SHA256 = 'f3de2ecb02869f2aaf89101c138efa3c1f1b7357655ca20f705d2636ec4306ee'
MIN_BINDINGS = 100


def ensure(config, offline=False, dry_run=False):
    target = config.path('controller', 'mapping')
    if not target.exists():
        if offline:
            raise Failure(f'Controller mapping missing: {target}',
                          'Run ./rx3 mapping with network access, or set [controller] mapping to your XML.')
        if dry_run:
            say(f'  [dry-run] would fetch {URL} to {target}')
            return
        with urllib.request.urlopen(URL, timeout=30) as response:
            data = response.read(1024 * 1024)
        if hashlib.sha256(data).hexdigest() != SHA256:
            raise Failure('Downloaded controller mapping checksum does not match; nothing installed')
        with Tree(target.parent, create=True) as tree:
            tree.write(target.name, data, 0o644, replace=False)
    spec = importlib.util.spec_from_file_location('rx3_mapping_check', REPO / 'ddj400-rx3.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        bridge = module.Bridge(str(target), lambda *a: None)
    except Exception as error:
        raise Failure(f'Cannot load controller mapping {target}: {error}')
    if len(bridge.mapping) < MIN_BINDINGS:
        raise Failure(f'Only {len(bridge.mapping)} supported DDJ-400 bindings found in {target}',
                      f'The complete pinned mapping provides at least {MIN_BINDINGS}. Move this old or\n'
                      'custom XML aside and run ./rx3 mapping again.')
    ok(f'Controller mapping: {len(bridge.mapping)} bindings from {target}')
