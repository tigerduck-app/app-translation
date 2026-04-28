# Missing Languages

Languages that exist in `generated/` but **not** in `source/`.

Codes are normalized to BCP 47-like form for comparison:
- Android `values-XX` → `XX`, `values-XX-rYY` → `XX-YY` (the bare `values` directory maps to `en`).
- Apple `XX.lproj` → `XX` (covers iOS, iPadOS, watchOS, macOS).

## Summary

| Platform                    | Missing count |
| --------------------------- | ------------- |
| Android                     | 148           |
| Apple (iOS/iPadOS/watchOS/macOS) | 148      |
| Missing on **both**         | 145           |

## Missing on both Android and Apple (145)

```
aa  ab  ae  af  ak  am  an  as  av  ay
az  ba  be  bh  bi  bm  bo  br  bs  ce
ch  co  cr  cu  cv  cy  dv  dz  ee  en-AU
en-CA  en-GB  en-IN  eo  es-MX  eu  fa  ff  fj  fo
fr-CA  fy  ga  gd  gl  gn  gv  ha  ho  ht
hy  hz  ia  ie  ig  ii  ik  io  iu  jv
ka  kg  ki  kj  kl  km  kr  ks  ku  kv
kw  ky  la  lb  lg  li  ln  lo  lu  mg
mh  mi  mk  mn  mt  my  na  nb  nd  ne
ng  nn  nr  nv  ny  oc  oj  om  or  os
pi  ps  pt  qu  rm  rn  rw  sa  sc  sd
se  sg  si  sm  sn  so  sq  ss  st  su
sw  tg  ti  tk  tn  to  ts  tt  tw  ty
ug  uz  ve  vo  wa  wo  xh  yo  za  zh-CN
zh-HK  zh-MO  zh-SG  zh-TW  zu
```

## Missing on Android only (3)

These are legacy/deprecated ISO 639-1 codes still emitted by Android tooling. The modern equivalents do exist in source.

| Android code | Modern code | In source? |
| ------------ | ----------- | ---------- |
| `in`         | `id` (Indonesian) | yes  |
| `iw`         | `he` (Hebrew)     | yes  |
| `ji`         | `yi` (Yiddish)    | no   |

## Missing on Apple only (3)

| Apple code | Note                                         | In source? |
| ---------- | -------------------------------------------- | ---------- |
| `tl`       | Tagalog (parent of `fil`); `fil` is in source | partial   |
| `yi`       | Yiddish                                       | no        |
| `zh`       | Generic Chinese (no script tag); source has `zh-Hans` and `zh-Hant` | partial |
