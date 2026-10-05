# Fase 4 — Baseline Unknown (2026-10-05)

**Unknown enabled global:** 834

## Por host

| Host | Unknown | item_disabled | item_unsupported | other |
| --- | ---: | ---: | ---: | ---: |
| SCL-TEC2-SW01 | 284 | 0 | 284 | 0 |
| SCL-TEC1-SW02 | 144 | 71 | 73 | 0 |
| SCL-TEC1-SW03 | 122 | 60 | 62 | 0 |
| SCL-CPD-SW01 | 2 | 0 | 2 | 0 |
| SPO-CPD-SW01 | 2 | 0 | 2 | 0 |
| BGP-SRV-VAPP10 | 11 | 2 | 9 | 0 |

## Padrões globais (amostra escopo)

- `item_unsupported`: 432
- `item_disabled`: 133

## Samples P1

### SCL-TEC2-SW01 (284)
**item_unsupported**
- `26229` Cisco IOS: Device has been replaced: Cannot evaluate function last(/SCL-TEC2-SW01/system.hw.serialnumber,#1): item is not supported.
- `26231` Cisco IOS: Operating system description has changed: Cannot evaluate function last(/SCL-TEC2-SW01/system.sw.os[sysDescr.0],#1): item is not supported.
- `35996` Cisco IOS: Interface gi2/0/19(Tear 259 (Picanol)): High bandwidth usage: Cannot evaluate function avg(/SCL-TEC2-SW01/net.if.in[ifHCInOctets.71],15m): item is not supported.

### SCL-TEC1-SW02 (144)
**item_unsupported**
- `26850` Cisco IOS: Device has been replaced: Cannot evaluate function last(/SCL-TEC1-SW02/system.hw.serialnumber,#1): item is not supported.
- `26852` Cisco IOS: Operating system description has changed: Cannot evaluate function last(/SCL-TEC1-SW02/system.sw.os[sysDescr.0],#1): item is not supported.
- `35680` Cisco IOS: Interface gi2/0/45(SCL-TEC1-UPS02): High error rate: Cannot evaluate function min(/SCL-TEC1-SW02/net.if.in.errors[ifInErrors.97],5m): item is not supported.
**item_disabled**
- `35568` Cisco IOS: Interface gi2/0/45(SCL-TEC1-UPS02): High bandwidth usage: Cannot evaluate function avg(/SCL-TEC1-SW02/net.if.in[ifHCInOctets.97],15m): item is disabled.
- `35569` Cisco IOS: Interface gi2/0/16(T810-102): High bandwidth usage: Cannot evaluate function avg(/SCL-TEC1-SW02/net.if.in[ifHCInOctets.68],15m): item is disabled.
- `35570` Cisco IOS: Interface gi1/0/45(T810-063): High bandwidth usage: Cannot evaluate function avg(/SCL-TEC1-SW02/net.if.in[ifHCInOctets.45],15m): item is disabled.

### SCL-TEC1-SW03 (122)
**item_unsupported**
- `26551` Cisco IOS: Device has been replaced: Cannot evaluate function last(/SCL-TEC1-SW03/system.hw.serialnumber,#1): item is not supported.
- `26553` Cisco IOS: Operating system description has changed: Cannot evaluate function last(/SCL-TEC1-SW03/system.sw.os[sysDescr.0],#1): item is not supported.
- `33734` Cisco IOS: Interface gi2/0/45(T810-046): High error rate: Cannot evaluate function min(/SCL-TEC1-SW03/net.if.in.errors[ifInErrors.97],5m): item is not supported.
**item_disabled**
- `33645` Cisco IOS: Interface gi2/0/45(T810-046): High bandwidth usage: Cannot evaluate function avg(/SCL-TEC1-SW03/net.if.in[ifHCInOctets.97],15m): item is disabled.
- `33646` Cisco IOS: Interface gi2/0/16(T810-053): High bandwidth usage: Cannot evaluate function avg(/SCL-TEC1-SW03/net.if.in[ifHCInOctets.68],15m): item is disabled.
- `33649` Cisco IOS: Interface gi2/0/13(T810-008): High bandwidth usage: Cannot evaluate function avg(/SCL-TEC1-SW03/net.if.in[ifHCInOctets.65],15m): item is disabled.
