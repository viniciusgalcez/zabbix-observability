# Matriz de correlações de links — 30/09/2026

- Correlações inventariadas: 59
- Regras que fecham eventos novos: 32
- Regras que fecham eventos antigos: 27
- Valores distintos de causa: 27

## Causas presentes em mais de duas regras

| Causa | Quantidade | Correlações |
| --- | ---: | --- |
| BRAS_ISP1 | 5 | 24 (close_new), 33 (close_new), 34 (close_old), 57 (close_new), 58 (close_old) |
| DENIM_ISP1 | 5 | 18 (close_new), 27 (close_new), 28 (close_old), 53 (close_new), 54 (close_old) |
| DENIM_ISP2 | 5 | 19 (close_new), 25 (close_new), 26 (close_old), 55 (close_new), 56 (close_old) |
| FIA_ISP1 | 5 | 22 (close_new), 29 (close_new), 30 (close_old), 49 (close_new), 50 (close_old) |
| FIA_ISP2 | 5 | 23 (close_new), 31 (close_new), 32 (close_old), 51 (close_new), 52 (close_old) |
| BGP_ISP1 | 4 | 7 (close_new), 20 (close_old), 39 (close_new), 40 (close_old) |
| BGP_ISP2 | 4 | 3 (close_new), 21 (close_old), 41 (close_new), 42 (close_old) |
| HK_VIVO | 4 | 11 (close_new), 12 (close_old), 35 (close_new), 36 (close_old) |
| SCL_ALGAR | 4 | 14 (close_new), 15 (close_old), 43 (close_new), 44 (close_old) |
| SPO_ALGAR | 4 | 8 (close_new), 13 (close_old), 47 (close_new), 48 (close_old) |
| SPO_VIVO | 4 | 16 (close_new), 17 (close_old), 45 (close_new), 46 (close_old) |

## Constatação do piloto

As correlações 16 e 45 para SPO/Vivo usam a operação `close_new`. Enquanto a causa permaneceu ativa, os sintomas persistentes foram encerrados e reabertos em cada nova avaliação. A amostra de 30/09 registrou 1.000 eventos no SCL em 83 minutos. O teste de desativação das duas regras deixou seis sintomas abertos uma única vez, confirmando o mecanismo de repetição. As regras foram restauradas porque a proteção temporária dos seis eventos no Teams não recebeu aprovação automática.

A planilha completa está em `reports/link-correlation-matrix-20260930.csv`.
