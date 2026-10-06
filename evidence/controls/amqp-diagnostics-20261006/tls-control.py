# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import socket,ssl
checks=0
for mode in ('trusted','wrong-ca','wrong-host','mtls-trusted','mtls-missing'):
 for i in range(4):
  context=ssl.create_default_context(cafile='/certs/'+('wrong-ca' if mode=='wrong-ca' else 'ca')+'.pem')
  if mode=='mtls-trusted':context.load_cert_chain('/certs/client.pem','/certs/client.key')
  error=None
  try:
   with socket.create_connection(('amqp-broker',5673 if mode.startswith('mtls') else 5671),timeout=5) as raw:
    with context.wrap_socket(raw,server_hostname='invalid.example' if mode=='wrong-host' else 'amqp-broker') as tls:
     tls.sendall(b'AMQP\x03\x01\x00\x00');data=tls.recv(8)
     assert data==b'AMQP\x03\x01\x00\x00',data
  except ssl.SSLError as e:error=e
  if mode in ('wrong-ca','wrong-host'):assert isinstance(error,ssl.SSLCertVerificationError),(mode,error)
  elif mode=='mtls-missing':assert error and error.reason=='SSLV3_ALERT_BAD_CERTIFICATE',(mode,error)
  else:assert error is None,(mode,error)
  checks+=1
  print(mode,i,'correct rejection: '+str(error) if error else 'accepted',flush=True)
print(checks,'standalone TLS controls passed')
