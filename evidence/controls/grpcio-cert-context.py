# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import io,json,logging,ssl,sys
from pathlib import Path
from pip._internal.cli.index_command import _create_truststore_ssl_context
from pip._vendor import certifi
capture=io.StringIO();handler=logging.StreamHandler(capture)
logger=logging.getLogger('pip._internal.cli.index_command');logger.addHandler(handler)
context=_create_truststore_ssl_context();logger.removeHandler(handler)
record={'phase':sys.argv[1],'context_created':context is not None,'messages':capture.getvalue(),
        'bundle':certifi.where(),'bundle_bytes':Path(certifi.where()).stat().st_size if Path(certifi.where()).exists() else None}
if context is not None:
    assert context.verify_mode==ssl.CERT_REQUIRED
    assert context.check_hostname
if sys.argv[1]=='provider-absent':
    assert context is None,record
    assert record['messages']=='Disabling truststore because of missing certificates\n',record
else:
    assert context is not None and not record['messages'],record
print(json.dumps(record))
