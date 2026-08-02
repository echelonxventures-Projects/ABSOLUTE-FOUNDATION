# UCOS-UTCE-001 · Derivation Headroom

How many lane entries the edges ALREADY in the certified corpus would support, and
how many of those the generator already wrote. `derivable, not written` is headroom
that requires no new evidence — only that the located generator write what its own
vocabulary already declares. **This programme writes none of it.** Every row cites
located edge identifiers so the count is auditable against the corpus.

| Rule | Located type | Read | Lane | Artifacts supported | Already written | Derivable, not written | Cited edges |
|---|---|---|---|---|---|---|---|
| `UTCE-DR-01` | `Parent` | from | `architecture` | 1193 | 251 | 942 | `UEDGE-000000002`, `UEDGE-000000005`, `UEDGE-000000907` |
| `UTCE-DR-02` | `Depends-On` | from | `architecture` | 296 | 222 | 74 | `UEDGE-000000001`, `UEDGE-000000004`, `UEDGE-000000007` |
| `UTCE-DR-03` | `Authorized-By` | from | `requirement` | 38 | 38 | 0 | `UEDGE-000003453`, `UEDGE-000003455`, `UEDGE-000003459` |
| `UTCE-DR-04` | `Implements` | from | `architecture` | 36 | 36 | 0 | `UEDGE-000002917`, `UEDGE-000002985`, `UEDGE-000003055` |
| `UTCE-DR-05` | `Implemented-By` | to | `implementation` | 36 | 4 | 32 | `UEDGE-000002918`, `UEDGE-000002986`, `UEDGE-000003056` |
| `UTCE-DR-06` | `Consumes` | from | `architecture` | 24 | 24 | 0 | `UEDGE-000002597`, `UEDGE-000002639`, `UEDGE-000002659` |
| `UTCE-DR-07` | `Traces-To` | from | `requirement` | 5 | 5 | 0 | `UEDGE-000002967`, `UEDGE-000003039`, `UEDGE-000003105` |

## Basis of each rule

| Rule | Basis |
|---|---|
| `UTCE-DR-01` | The located vocabulary declares this type's subject lane to be the architecture lane; the structural edges already exist in the certified corpus but the generator writes no lane entry for them. |
| `UTCE-DR-02` | Declared subject lane in the located vocabulary. |
| `UTCE-DR-03` | Declared subject lane in the located vocabulary. |
| `UTCE-DR-04` | Declared subject lane in the located vocabulary. |
| `UTCE-DR-05` | Declared object lane of the located Implements type; read from the inverse edge. |
| `UTCE-DR-06` | Declared subject lane in the located vocabulary. |
| `UTCE-DR-07` | Declared subject lane in the located vocabulary. |
