# VQA Error Analysis

Samples in promoted evaluation: **72**
Wrong/non-exact rows: **48**

## By dataset

- VRSBench: 3 wrong/non-exact out of 4
- CDVQA: 1 wrong/non-exact out of 4
- RSVQA: 44 wrong/non-exact out of 64

## Most common expected → predicted pairs

- `no` → `yes`: 15
- `yes` → `no`: 14
- `0` → `4`: 2
- `Yellow` → `white`: 1
- `2` → `3`: 1
- `North-South` → `straight`: 1
- `urban` → `rural`: 1
- `2` → `1`: 1
- `3` → `0`: 1
- `138` → `2`: 1
- `850` → `3`: 1
- `348` → `0`: 1
- `0` → `1`: 1
- `0` → `12`: 1
- `87` → `3`: 1
- `0` → `lot`: 1
- `0` → `2`: 1
- `3049` → `3`: 1
- `6` → `3`: 1
- `62` → `3`: 1

## Priority

Focus model work on repeated systematic answer confusions. Do not tune against held-out evaluation labels directly; use separate training/validation data.